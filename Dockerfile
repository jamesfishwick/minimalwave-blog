# Dockerfile for Minimal Wave Blog

# Use an official Python runtime as a parent image
FROM python:3.10-slim

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

# Expose the port the app runs on
EXPOSE 8000

# Don't run collectstatic here - it will be run in the entrypoint script
# This ensures the correct settings are loaded when collecting static files

# Set environment variable to determine which settings to use
# This can be overridden during build with --build-arg
ARG DJANGO_SETTINGS_MODULE=minimalwave-blog.settings.development
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}

# Define the entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

# Define the command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
