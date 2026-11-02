#!/usr/bin/env bash
# One-time setup of an Ubuntu/Debian server: Apache + PHP + certbot, vhost for the site.
# Usage: sudo DOMAIN=truebuiltgroupllc.com CERTBOT_EMAIL=you@example.com DEPLOY_PATH=/var/www/truebuiltgroupllc.com scripts/setup-server.sh
set -euo pipefail
: "${DOMAIN:?set DOMAIN}"; : "${CERTBOT_EMAIL:?set CERTBOT_EMAIL}"
DEPLOY_PATH="${DEPLOY_PATH:-/var/www/$DOMAIN}"

apt-get update
apt-get install -y apache2 php libapache2-mod-php php-curl php-mbstring certbot python3-certbot-apache
a2enmod rewrite headers expires deflate
a2enmod brotli 2>/dev/null || true

mkdir -p "$DEPLOY_PATH/public"
cat > "/etc/apache2/sites-available/$DOMAIN.conf" <<CONF
<VirtualHost *:80>
  ServerName $DOMAIN
  ServerAlias www.$DOMAIN
  DocumentRoot $DEPLOY_PATH/public
  <Directory $DEPLOY_PATH/public>
    AllowOverride All
    Require all granted
  </Directory>
  ErrorLog \${APACHE_LOG_DIR}/$DOMAIN-error.log
  CustomLog \${APACHE_LOG_DIR}/$DOMAIN-access.log combined
</VirtualHost>
CONF
a2ensite "$DOMAIN.conf"
a2dissite 000-default.conf || true
systemctl reload apache2

certbot --apache --non-interactive --agree-tos -m "$CERTBOT_EMAIL" -d "$DOMAIN" -d "www.$DOMAIN" --redirect
echo "Done. Put the .env file at $DEPLOY_PATH/.env (outside public/)."
