#!/usr/bin/env bash
# Builds the site and serves it locally with Apache-like clean URLs via PHP's built-in server.
# Usage: scripts/preview.sh  then open http://localhost:${PREVIEW_PORT:-8080}
set -euo pipefail
cd "$(dirname "$0")/.."
python3 build/build.py
PORT="${PREVIEW_PORT:-8080}"
echo "Serving http://localhost:$PORT"
php -S "localhost:$PORT" -t public scripts/router.php
