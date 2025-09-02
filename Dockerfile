FROM python:3.12-slim as builder


ENV VENV_PATH=/opt/venv \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt requirements.txt
RUN python -m venv $VENV_PATH \
 && $VENV_PATH/bin/pip install --upgrade pip \
 && $VENV_PATH/bin/pip install -r requirements.txt

FROM python:3.12-slim as app


ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY . .
CMD ["uvicorn", "src.main:app", "--host","0.0.0.0", "--port", "8000"]