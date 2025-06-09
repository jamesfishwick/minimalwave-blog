# Dockerfile for Minimal Wave Blog

# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    cron \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Create a symlink for python if it doesn't exist
RUN ln -sf $(which python3) /usr/local/bin/python

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* /app/

# Install project dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the project code into the container
COPY . /app/

# Make sure the entrypoint script uses LF line endings
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh && \
    rm -rf /var/lib/apt/lists/*

# Expose the port the app runs on
EXPOSE 8000

# Set environment variable to determine which settings to use
ARG DJANGO_SETTINGS_MODULE=minimalwave_blog.settings.development
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}

# Use shell form for entrypoint to ensure proper shell interpretation
ENTRYPOINT ["/bin/bash", "/app/docker-entrypoint.sh"]

# Replace the CMD to use Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "minimalwave_blog.wsgi:application"]
