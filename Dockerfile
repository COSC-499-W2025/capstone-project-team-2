# Use Python 3.11 slim image as base
FROM python:3.11-bookworm

# Set working directory in container
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Copy requirements.txt
COPY src/requirements.txt .

# Installation of Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY src/ .

# Set environment variable (for GUI)
ENV DISPLAY=:0

# Command to run your application (change 'main.py' to your entry point)
CMD ["python", "src/main.py"]