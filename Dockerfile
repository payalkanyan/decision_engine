FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir . "groq>=0.4.0" && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["python", "-m", "api.main"]
