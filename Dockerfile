# Use an official Python base image
FROM python:3.12-slim

# Install system build dependencies needed for compiling packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Set command to run your app (change as needed)
CMD ["python", "app.py"]
