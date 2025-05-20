# Use official Python 3.12 slim image
FROM python:3.12-slim



RUN python -m pip install --upgrade pip setuptools wheel
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_BUILD_ISOLATION=1
RUN pip install -r requirements.txt
# Install system packages needed to build packages like numpy
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy your app files and requirements.txt into container
COPY . /app

# Upgrade pip, setuptools, wheel first to latest versions (fixes Python 3.12 setuptools issues)
RUN python -m pip install --upgrade pip setuptools wheel

# Now install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Default command to run your app (change as needed)
CMD ["python", "app.py"]
