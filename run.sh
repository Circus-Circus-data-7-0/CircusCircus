#!/usr/bin/env bash
set -e

# Always run from this script's directory.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment on first run.
if [ ! -d ".venv" ]; then
	python3 -m venv .venv
fi

. .venv/bin/activate
pip install -r requirements.txt >/dev/null

export SECRET_KEY="${SECRET_KEY:-kristofer}"
export PORT="${PORT:-8000}"

# MySQL-only configuration.
export DB_USER="${DB_USER:-zipchat_app}"
export DB_HOST="${DB_HOST:-127.0.0.1}"
export DB_PORT="${DB_PORT:-3306}"
export DB_NAME="${DB_NAME:-ZipChat}"
export DB_PASSWORD="${DB_PASSWORD:-password}"

echo "Starting with MySQL database: $DB_NAME"

#flask run --port "$PORT"

if [ "$1" = "--server" ]; then
    cd ./forum && flask run --host=0.0.0.0 --port="$PORT"
else
    cd ./forum && flask run --port="$PORT"
fi

# To run the server, use: ./run.sh --server
# To run the server in development mode, use: ./run.sh
