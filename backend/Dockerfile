FROM python:3.12-slim-bookworm

WORKDIR /app

COPY backend/pyproject.toml ./
COPY backend/app ./app

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
