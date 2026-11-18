#!/usr/bin/env bash
# CricAnalyze one-time setup for a Hostinger VPS (Ubuntu 22.04 / 24.04). Run as root:
#   git clone https://github.com/<you>/<repo>.git /opt/cricanalyze && cd /opt/cricanalyze && sudo bash deploy/hostinger/setup.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
APP_USER=cricanalyze
DATA_DIR=/var/lib/cricanalyze
EI_INDEX=https://d33sy5i8bnduwe.cloudfront.net/simple/

[ "$(id -u)" = 0 ] || { echo "Run with sudo/root."; exit 1; }
. /etc/os-release
case "$VERSION_CODENAME" in jammy|noble) ;; *) echo "Ubuntu 22.04 or 24.04 required (found $PRETTY_NAME)."; exit 1;; esac

read -rp "Domain [cricanalyze.in]: " DOMAIN; DOMAIN=${DOMAIN:-cricanalyze.in}
read -rp "Email for SSL certificate + super admin [cricanalyze.in@gmail.com]: " ADMIN_EMAIL; ADMIN_EMAIL=${ADMIN_EMAIL:-cricanalyze.in@gmail.com}

echo "==> System packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y software-properties-common curl gnupg git nginx certbot python3-certbot-nginx build-essential libgl1 libglib2.0-0 ufw
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3.11-dev

echo "==> Node.js 20 + Yarn"
if ! command -v node >/dev/null || [ "$(node -v | cut -d. -f1 | tr -d v)" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi
corepack enable

echo "==> MongoDB 8.0"
if ! command -v mongod >/dev/null; then
  curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
  echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu $VERSION_CODENAME/mongodb-org/8.0 multiverse" > /etc/apt/sources.list.d/mongodb-org-8.0.list
  apt-get update -y
  apt-get install -y mongodb-org
fi
systemctl enable --now mongod

echo "==> App user + folders"
id -u $APP_USER >/dev/null 2>&1 || useradd --system --home "$DATA_DIR" --shell /usr/sbin/nologin $APP_USER
mkdir -p "$DATA_DIR/storage" "$DATA_DIR/backups"
chown -R $APP_USER:$APP_USER "$DATA_DIR" "$APP_DIR"

echo "==> Backend .env"
ENV_FILE="$APP_DIR/backend/.env"
if [ ! -f "$ENV_FILE" ] || ! grep -q "^STORAGE_BACKEND=local" "$ENV_FILE"; then
  echo "Enter your keys (input is hidden for secrets). Press Enter to skip any you don't have yet - you can add them later in $ENV_FILE"
  read -rsp "Anthropic API key: " K_ANTH; echo
  read -rp  "SMTP user [noreply@$DOMAIN]: " K_SMTP_USER; K_SMTP_USER=${K_SMTP_USER:-noreply@$DOMAIN}
  read -rsp "SMTP password (Hostinger mailbox): " K_SMTP_PASS; echo
  read -rp  "Razorpay Key ID: " K_RZP_ID
  read -rsp "Razorpay Key Secret: " K_RZP_SECRET; echo
  read -rsp "Razorpay Webhook Secret (optional): " K_RZP_WH; echo
  cat > "$ENV_FILE" <<EOF
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=cricanalyze
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
APP_URL=https://$DOMAIN
APP_SECRET=$(openssl rand -hex 32)
ADMIN_EMAIL=$ADMIN_EMAIL
COOKIE_SECURE=true
DEV_EMAIL_OUTBOX=false
STORAGE_BACKEND=local
STORAGE_DIR=$DATA_DIR/storage
VIDEO_STORAGE_BUCKET=cricanalyze
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=465
SMTP_SECURE=ssl
SMTP_USER=$K_SMTP_USER
SMTP_PASS=$K_SMTP_PASS
SMTP_FROM_EMAIL=$K_SMTP_USER
SMTP_FROM_NAME=CricAnalyze
ANTHROPIC_API_KEY=$K_ANTH
AI_INFERENCE_PROVIDER=vision_llm
AI_MODEL=claude-sonnet-5-5
RAZORPAY_KEY_ID=$K_RZP_ID
RAZORPAY_KEY_SECRET=$K_RZP_SECRET
RAZORPAY_WEBHOOK_SECRET=$K_RZP_WH
EOF
  chown $APP_USER:$APP_USER "$ENV_FILE"; chmod 600 "$ENV_FILE"
else
  echo "Keeping existing $ENV_FILE"
fi

echo "==> Build app"
DOMAIN="$DOMAIN" bash "$APP_DIR/deploy/hostinger/build.sh"

echo "==> Service + web server"
sed "s#__APP_DIR__#$APP_DIR#g" "$APP_DIR/deploy/hostinger/cricanalyze.service" > /etc/systemd/system/cricanalyze.service
sed "s#__APP_DIR__#$APP_DIR#g; s#__DOMAIN__#$DOMAIN#g" "$APP_DIR/deploy/hostinger/nginx.conf" > /etc/nginx/sites-available/cricanalyze
ln -sf /etc/nginx/sites-available/cricanalyze /etc/nginx/sites-enabled/cricanalyze
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
systemctl daemon-reload && systemctl enable --now cricanalyze

echo "==> Firewall"
ufw allow OpenSSH >/dev/null; ufw allow 'Nginx Full' >/dev/null; ufw --force enable >/dev/null

echo "==> Daily backup (03:30): database + uploaded files, keeps 7 days"
cat > /etc/cron.d/cricanalyze-backup <<EOF
30 3 * * * root mongodump --quiet --db cricanalyze --archive=$DATA_DIR/backups/db-\$(date +\%F).gz --gzip && tar -czf $DATA_DIR/backups/files-\$(date +\%F).tgz -C $DATA_DIR storage && find $DATA_DIR/backups -mtime +7 -delete
EOF

echo "==> SSL certificate"
if certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m "$ADMIN_EMAIL" --redirect; then
  echo "SSL ready."
else
  echo "!! SSL failed - check that the A records for $DOMAIN and www.$DOMAIN point to this VPS, then run:"
  echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --redirect"
fi

sleep 3
curl -fsS http://127.0.0.1:8001/api/health && echo && echo "Done. Open https://$DOMAIN" || echo "Backend not healthy yet - see: sudo journalctl -u cricanalyze -n 100"
