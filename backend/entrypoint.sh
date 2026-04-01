#!/usr/bin/env sh
set -e

echo "Running database migrations..."
python3 -c "
import subprocess, sys
try:
    subprocess.run(['alembic', 'upgrade', 'head'], timeout=60, check=True)
    print('Migrations complete.')
except subprocess.TimeoutExpired:
    print('WARNING: migration timed out after 60s — continuing startup')
except subprocess.CalledProcessError as e:
    print(f'WARNING: migration failed (exit {e.returncode}) — continuing startup')
"

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
