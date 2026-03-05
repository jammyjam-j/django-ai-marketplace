FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev libc6-dev git ca-certificates curl gnupg2 && \
    pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir && \
    rm -rf /var/lib/apt/lists/*

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]