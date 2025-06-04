#!/bin/bash
if [ "$RUN_MODE" = "cron" ]; then
  echo "Running in cron mode"
  python3 main.py --cron
else
  echo "Running in web server mode"
  gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 4 --timeout 120 main:app
fi
