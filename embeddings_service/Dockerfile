# embeddings_service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --default-timeout=1000 --retries 10 --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 9000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
