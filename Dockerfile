FROM python:3.13-slim

ENV PROMETHEUS_MULTIPROC_DIR /dev/shm

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock README.md ./

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --without dev --no-root

# Copy application code
COPY src ./

# Install application
RUN poetry install --no-interaction --no-ansi --without dev

# Set user
RUN useradd -ms /bin/bash appuser
USER appuser

# Command to run the application
CMD ["uvicorn", "esg_fastapi.wsgi:app", "--host", "0.0.0.0", "--port", "1337", "--reload"]
