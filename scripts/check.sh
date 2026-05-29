#!/usr/bin/env sh
set -eu

PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-.cache/pycache}" python3 -m compileall apps/backend/app apps/rpa-worker/worker
npm --prefix apps/frontend run build
