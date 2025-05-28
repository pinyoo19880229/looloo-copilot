# Stage 1: Build the application
FROM python:3.9-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only files necessary for installing dependencies
COPY pyproject.toml poetry.lock* ./

# Install dependencies
# --no-root: Do not install the project itself as editable, install dependencies only
# --no-dev: Do not install development dependencies
RUN poetry install --no-root --no-dev

# Stage 2: Create the runtime image
FROM python:3.9-slim

WORKDIR /app

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed dependencies from the builder stage
COPY --from=builder /app/.venv /.venv

# Copy the application code
COPY ./app ./app

# Set environment variables for Python
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
