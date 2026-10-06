FROM python:3.12-slim

# Create non-root user
RUN groupadd -r aegis && useradd -r -g aegis aegis

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY .env.example .env.example

RUN chown -R aegis:aegis /app
USER aegis

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
