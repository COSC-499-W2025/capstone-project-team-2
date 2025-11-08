# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies for GUI support
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        python3-tk \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libsm6 \
        libice6 \
        libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/*


# Copy requirements.txt
COPY src/requirements.txt .

# Installation of Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY src/ .

# Set environment variable (for GUI)
ENV DISPLAY=:0
ENV PYTHONUNBUFFERED=1

# Command to run your application (change 'main.py' to your entry point)
CMD ["python", "main.py"]