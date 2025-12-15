# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Prevent Python from creating __pycache__/ *.pyc files inside the container
ENV PYTHONDONTWRITEBYTECODE=1

# (Optional) Print logs immediately (no buffering), nicer for Docker logs
ENV PYTHONUNBUFFERED=1

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]