#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Run the app in debug mode with verbose logging
uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload \
    --reload-dir ./app \
    --reload-dir ./data \
    --reload-dir ./static \
    --reload-dir ./templates \
    --reload-include '*.py' \
    --reload-include '*.csv' \
    --reload-include '*.html' \
    --reload-include '*.css' \
    --reload-include '*.svg' \
    --log-level trace