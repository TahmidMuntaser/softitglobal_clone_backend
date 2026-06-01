#!/usr/bin/env bash
VENV="$(dirname "$0")/../.venv/bin/python"
"$VENV" "$(dirname "$0")/../manage.py" runserver
