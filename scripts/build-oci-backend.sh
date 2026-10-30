#!/usr/bin/env bash
# Prepare the Python API/runtime on an OCI Linux VM. Does NOT deploy or provision resources.
set -euo pipefail
if [ "${EUID:-$(id -u)}" -eq 0 ]; then
  echo "Run as a non-root build user; do not install project dependencies as root." >&2
  exit 1
fi
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3.12 is required (set PYTHON_BIN if installed under a different name)." >&2
  exit 1
fi
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install -r apps/api/requirements.txt -r apps/api/requirements-firebase.txt
.venv/bin/python -c 'import fastapi, celery, psycopg, redis; print("AEGIS API dependency import check passed")'
printf '%s\n' "Python backend prepared. No OCI services, firewall rules, database, secrets, deployments, or migrations were configured."
