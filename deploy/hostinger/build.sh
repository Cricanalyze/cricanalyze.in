#!/usr/bin/env bash
# Installs backend packages and builds the website. Used by setup.sh and update.sh.
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
APP_USER=cricanalyze
EI_INDEX=https://d33sy5i8bnduwe.cloudfront.net/simple/
DOMAIN="${DOMAIN:-$(grep -E '^APP_URL=' "$APP_DIR/backend/.env" | sed -E 's#^APP_URL=https?://##; s#/.*##')}"

echo "==> Backend packages"
[ -d "$APP_DIR/venv" ] || python3.11 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q --upgrade pip wheel
grep -viE '^(emergentintegrations|litellm)' "$APP_DIR/backend/requirements.txt" > /tmp/cricanalyze-req.txt
"$APP_DIR/venv/bin/pip" install -q -r /tmp/cricanalyze-req.txt "emergentintegrations==0.2.2" --extra-index-url "$EI_INDEX"

echo "==> Website build for https://$DOMAIN"
cd "$APP_DIR/frontend"
yarn install --frozen-lockfile --network-timeout 600000 || yarn install --network-timeout 600000
REACT_APP_BACKEND_URL="https://$DOMAIN" NODE_OPTIONS=--max-old-space-size=3072 GENERATE_SOURCEMAP=false yarn build

chown -R $APP_USER:$APP_USER "$APP_DIR"
