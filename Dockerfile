FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (required for some python packages and networking tools)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    iputils-ping \
    nmap \
    snmp \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# We will run gunicorn in docker-compose, so no CMD here.
