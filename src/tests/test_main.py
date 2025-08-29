import pytest_asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from src.db.models import Base, Question
from src.db.db_config import make_session
from httpx import ASGITransport, AsyncClient
from main import app as fastapi_app
from datetime import datetime
from fastapi import status
from sqlalchemy import select


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
async def test_create_question_success(client, test_session):
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
