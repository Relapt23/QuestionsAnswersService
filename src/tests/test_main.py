import pytest_asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from src.db.models import Base, Question, Answer
from src.db.db_config import make_session
from httpx import ASGITransport, AsyncClient
from main import app as fastapi_app
from datetime import datetime
from fastapi import status
from sqlalchemy import select, text


@pytest_asyncio.fixture()
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture()
async def test_session(test_engine):
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        test_sess = async_sessionmaker(bind=conn, expire_on_commit=False)

        async def override_session() -> AsyncSession:
            async with test_sess() as s:
                yield s

        fastapi_app.dependency_overrides[make_session] = override_session
        try:
            async with test_sess() as session:
                yield session
        finally:
            await trans.rollback()
            fastapi_app.dependency_overrides.pop(make_session, None)


@pytest_asyncio.fixture()
async def client(test_session):
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_get_questions(client, test_session):
    # given
    questions_params1 = Question(
        text="test1", created_at=datetime(2025, 8, 20, 12, 0, 0)
    )
    questions_params2 = Question(
        text="test2", created_at=datetime(2025, 8, 21, 12, 0, 0)
    )
    questions_params3 = Question(
        text="test3", created_at=datetime(2025, 8, 1, 12, 0, 0)
    )
    test_session.add_all([questions_params1, questions_params2, questions_params3])

    await test_session.commit()

    # when
    response = await client.get("/questions/")
    data = response.json()

    # then
    assert response.status_code == 200
    assert [item["text"] for item in data] == ["test2", "test1", "test3"]


@pytest.mark.asyncio
async def test_create_question(client, test_session):
    # given
    questions_params = {"text": " test_text "}

    # when
    response = await client.post("/questions/", json=questions_params)
    data = response.json()

    questions = (
        await test_session.execute(select(Question).where(Question.id == data["id"]))
    ).scalar_one_or_none()

    # then
    assert response.status_code == status.HTTP_201_CREATED
    assert set(data.keys()) == {"id", "text", "created_at"}
    assert isinstance(data["id"], int)
    assert data["text"] == "test_text"
    assert questions is not None
    assert questions.text == "test_text"


@pytest.mark.asyncio
async def test_get_question_with_answers_404(client):
    # when
    response = await client.get("/questions/999999")
    # then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "question_not_found"


@pytest.mark.asyncio
async def test_get_question_with_answers_no_answers(client, test_session):
    # given
    questions_params = Question(text="why?")

    test_session.add(questions_params)
    await test_session.commit()

    # when
    response = await client.get(f"/questions/{questions_params.id}")
    data = response.json()

    # then
    assert response.status_code == status.HTTP_200_OK
    assert data["id"] == questions_params.id
    assert data["text"] == "why?"
    assert data["answers"] == []


@pytest.mark.asyncio
async def test_get_question_with_answers_with_answers(client, test_session):
    # given
    questions_params = Question(text="test_question")

    test_session.add(questions_params)
    await test_session.flush()

    answer1 = Answer(
        question_id=questions_params.id,
        user_id="test_id1",
        text="test_answer1",
        created_at=datetime(2025, 8, 20, 12, 0, 0),
    )
    answer2 = Answer(
        question_id=questions_params.id,
        user_id="test_id2",
        text="test_answer2",
        created_at=datetime(2025, 8, 21, 12, 0, 0),
    )

    test_session.add_all([answer1, answer2])
    await test_session.commit()

    # when
    response = await client.get(f"/questions/{questions_params.id}")
    data = response.json()

    # then
    assert response.status_code == status.HTTP_200_OK
    assert data["id"] == questions_params.id
    assert data["text"] == "test_question"
    assert len(data["answers"]) == 2

    texts = {ans["text"] for ans in data["answers"]}
    users = {ans["user_id"] for ans in data["answers"]}

    assert texts == {"test_answer1", "test_answer2"}
    assert users == {"test_id1", "test_id2"}

    for ans in data["answers"]:
        assert ans["question_id"] == questions_params.id
        assert isinstance(ans["id"], int)


@pytest.mark.asyncio
async def test_delete_question_404(client):
    # when
    response = await client.delete("/questions/999999")
    # then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "question_not_found"


@pytest.mark.asyncio
async def test_delete_question_success(client, test_session):
    # given
    questions_params = Question(
        text="test text", created_at=datetime(2025, 8, 20, 12, 0, 0)
    )

    test_session.add(questions_params)
    await test_session.commit()

    assert (
        await test_session.execute(
            select(Question).where(Question.id == questions_params.id)
        )
    ).scalar_one_or_none() is not None

    # when
    response = await client.delete(f"/questions/{questions_params.id}")

    # then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert (
        await test_session.execute(
            select(Question).where(Question.id == questions_params.id)
        )
    ).scalar_one_or_none() is None

    response2 = await client.delete(f"/questions/{questions_params.id}")
    assert response2.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_question_with_answers(client, test_session):
    # given
    await test_session.execute(text("PRAGMA foreign_keys=ON"))

    questions_params = Question(text="test text")

    test_session.add(questions_params)
    await test_session.flush()

    answer1 = Answer(
        question_id=questions_params.id,
        user_id="test_id1",
        text="test_answer1",
        created_at=datetime(2025, 8, 21, 10, 0, 0),
    )
    answer2 = Answer(
        question_id=questions_params.id,
        user_id="test_id2",
        text="test_answer2",
        created_at=datetime(2025, 8, 21, 11, 0, 0),
    )

    test_session.add_all([answer1, answer2])
    await test_session.commit()

    answers_before = (
        (
            await test_session.execute(
                select(Answer.id).where(Answer.question_id == questions_params.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(answers_before) == 2

    # when
    response = await client.delete(f"/questions/{questions_params.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # then
    assert (
        await test_session.execute(
            select(Question).where(Question.id == questions_params.id)
        )
    ).scalar_one_or_none() is None

    answers_after = (
        (
            await test_session.execute(
                select(Answer.id).where(Answer.question_id == questions_params.id)
            )
        )
        .scalars()
        .all()
    )
    assert answers_after == []


@pytest.mark.asyncio
async def test_create_answer_question_not_found(client):
    # given
    answer_params = {"user_id": "test_id1", "text": " test text"}

    # when
    response = await client.post("/questions/999999/answers/", json=answer_params)

    # then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "question_not_found"


@pytest.mark.asyncio
async def test_create_answer_success(client, test_session):
    # given
    questions_params = Question(text=" test text ")

    test_session.add(questions_params)
    await test_session.commit()

    answer_params = {"user_id": "test_id", "text": "test_answer"}

    # when
    response = await client.post(
        f"/questions/{questions_params.id}/answers/", json=answer_params
    )
    data = response.json()

    db_answer = (
        await test_session.execute(select(Answer).where(Answer.id == data["id"]))
    ).scalar_one_or_none()

    # then
    assert response.status_code == status.HTTP_201_CREATED
    assert set(data.keys()) == {"id", "question_id", "user_id", "text", "created_at"}
    assert isinstance(data["id"], int)
    assert data["question_id"] == questions_params.id
    assert data["user_id"] == answer_params["user_id"]
    assert data["text"] == "test_answer"

    assert db_answer is not None
    assert db_answer.question_id == questions_params.id
    assert db_answer.user_id == answer_params["user_id"]
    assert db_answer.text == "test_answer"


@pytest.mark.asyncio
async def test_get_answer_not_found(client):
    # when
    response = await client.get("/answers/999999")
    # then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "answer_not_found"


@pytest.mark.asyncio
async def test_get_answer_success(client, test_session):
    # given
    questions_params = Question(text="test text ")

    test_session.add(questions_params)
    await test_session.commit()

    answer = Answer(
        question_id=questions_params.id, user_id="test_id", text="test answer"
    )

    test_session.add(answer)
    await test_session.commit()

    answer_id = answer.id

    # when
    response = await client.get(f"/answers/{answer_id}")
    data = response.json()

    db_answer = (
        await test_session.execute(select(Answer).where(Answer.id == data["id"]))
    ).scalar_one_or_none()

    # then
    assert response.status_code == status.HTTP_200_OK
    assert set(data.keys()) == {"id", "question_id", "user_id", "text", "created_at"}
    assert data["id"] == answer_id
    assert data["question_id"] == questions_params.id
    assert data["user_id"] == "test_id"
    assert data["text"] == "test answer"

    assert db_answer is not None
    assert db_answer.question_id == questions_params.id
    assert db_answer.user_id == "test_id"
    assert db_answer.text == "test answer"


