FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy project
COPY . /app/

# Generate version file from Git metadata
RUN python scripts/write_version_file.py

# Create a non-root user with home directory and proper permissions
RUN groupadd -r django && useradd -r -g django -m -d /home/django django && \
    mkdir -p /app/staticfiles && \
    chown -R django:django /app && \
    chown -R django:django /home/django && \
    chmod -R 755 /home/django

USER django

# Set up Python user packages directory
ENV PATH="/home/django/.local/bin:$PATH"

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "DjangoBoilerplate.wsgi:application", "--bind", "0.0.0.0:8000"]