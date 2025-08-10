# Use a specific, official Python base image
FROM python:3.11.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Create and set the working directory
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# Install system dependencies that might be needed
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install packages
# Using --no-cache-dir ensures a clean install every time
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app will run on
EXPOSE 10000

# Set the command to run the application
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "app:app", "--bind", "0.0.0.0:10000"]
