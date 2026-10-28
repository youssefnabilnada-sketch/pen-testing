#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r apps/api/requirements.txt -r apps/api/requirements-firebase.txt
npm --prefix apps/web ci
API_INTERNAL_URL=http://127.0.0.1:8000 npm --prefix apps/web run build
mkdir -p apps/web/.next/standalone/.next
cp -R apps/web/.next/static apps/web/.next/standalone/.next/
if [ -d apps/web/public ]; then cp -R apps/web/public apps/web/.next/standalone/; fi
printf '%s\n' 'Build completed. No deployment, migrations or cloud connection has been claimed.'
