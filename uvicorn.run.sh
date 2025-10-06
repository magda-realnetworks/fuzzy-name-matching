#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Run the app in debug mode with verbose logging
uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload \
    --log-level trace
