FROM python:3.12-slim

# Disable Python bytecode generation and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a dedicated non-root user with no home directory and no shell
RUN groupadd -r aegis && useradd -r -g aegis -s /sbin/nologin aegis

WORKDIR /app

# Install dependencies as root before dropping privileges
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
# Provide the example env so pydantic-settings can find .env.example for docs;
# the real .env is never baked into the image — it is injected at runtime.
COPY .env.example .env.example

# Drop privileges
RUN chown -R aegis:aegis /app
USER aegis

# Use exec form so signals (SIGTERM) reach uvicorn directly
CMD ["uvicorn", "backend.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--no-access-log"]
