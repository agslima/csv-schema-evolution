# Use an official Python runtime as a parent image
FROM python:3.14-slim

# 2. Environment Variables (Security & Performance)
# Prevents Python from writing .pyc files (read-only filesystem compat)
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout/stderr (ensures logs are flushed immediately)
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# 4. Security: Create a non-root user
# We create a system group 'appgroup' and user 'appuser'
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Code
# We copy the 'backend' folder content into '/app'
# CRITICAL: We change ownership to the non-root user immediately
COPY --chown=appuser:appgroup . .

# 7. Security: Switch to Non-Root User
# From this point on, the container runs as 'appuser'
USER appuser

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application using Uvicorn
# 0.0.0.0 is required for the container to be accessible from outside
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
