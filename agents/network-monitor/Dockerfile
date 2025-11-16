FROM python:3.12-alpine AS builder
WORKDIR /app
RUN apk add --no-cache gcc musl-dev libffi-dev
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-alpine
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata curl iputils

COPY --from=builder /root/.local /usr/local

RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

ENV PYTHONPATH=/app/src

COPY src/ ./src/
RUN chown -R appuser:appuser /app

USER appuser
CMD ["python", "-m", "src.main"]