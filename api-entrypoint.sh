#!/bin/sh
set -e  # Exit if any command fails

echo "🚀 Running database migrations..."
uv run flask db upgrade

echo "🔥 Starting Gunicorn server with auto-reload..."
uv run gunicorn --reload -w 4 -b 0.0.0.0:5000 src.app:app
