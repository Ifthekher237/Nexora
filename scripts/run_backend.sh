#!/usr/bin/env bash
set -e

uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
