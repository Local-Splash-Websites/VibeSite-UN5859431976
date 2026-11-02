#!/usr/bin/env bash
# Builds the site and uploads public/ to the server over SSH.
# Usage: scripts/deploy.sh   (reads DEPLOY_* from .env)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
: "${DEPLOY_HOST:?set DEPLOY_HOST}"; : "${DEPLOY_USER:?set DEPLOY_USER}"; : "${DEPLOY_PATH:?set DEPLOY_PATH}"
python3 build/build.py --strict
rsync -az --delete -e "ssh -p ${DEPLOY_PORT:-22}" public/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/public/"
echo "Deployed to $DEPLOY_HOST:$DEPLOY_PATH/public"
