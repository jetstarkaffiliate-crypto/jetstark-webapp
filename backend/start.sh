#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create uploads directory if using default path
mkdir -p "${UPLOAD_DIR:-uploads/products}"

# Start the application
echo "Starting Jetstark API..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
