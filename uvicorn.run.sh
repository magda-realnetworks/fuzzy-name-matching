#!/bin/bash
# Simple script to run the FastAPI app with auto-reload

uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload
