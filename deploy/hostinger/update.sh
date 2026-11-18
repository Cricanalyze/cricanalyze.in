#!/usr/bin/env bash
# Pull the latest code from GitHub, rebuild and restart. Run: sudo bash /opt/cricanalyze/deploy/hostinger/update.sh
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$APP_DIR"
git config --global --add safe.directory "$APP_DIR"
git pull --ff-only
bash deploy/hostinger/build.sh
systemctl restart cricanalyze
sleep 3
curl -fsS http://127.0.0.1:8001/api/health && echo && echo "Updated." || echo "Backend not healthy - see: sudo journalctl -u cricanalyze -n 100"
