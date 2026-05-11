#!/bin/bash

# Wait for DB to be ready
echo "Waiting for database..."
# (Already handled by depends_on healthcheck in docker-compose, but good to have)

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Start application
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
