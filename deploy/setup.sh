#!/bin/bash
set -euo pipefail

echo "🚀 Setting up APFA-Prod on fresh DigitalOcean Droplet (IP: 67.205.140.55)"

apt-get update
apt-get upgrade -y
apt-get install -y \\
  docker.io \\
  docker-compose \\
  nginx-full \\
  nodejs \\
  npm \\
  git \\
  curl \\
  software-properties-common \\
  certbot \\
  python3-certbot-nginx

systemctl daemon-reload
systemctl start docker nginx
systemctl enable docker nginx

usermod -aG docker root

mkdir -p /opt/apfa-prod /var/www/apfa
chown -R www-data:www-data /var/www/apfa

cd /opt
rm -rf apfa-prod
git clone https://github.com/PhoenixWild29/APFA-Prod.git apfa-prod
cd apfa-prod

cp .env.example .env
echo \"# TODO: Edit /opt/apfa-prod/.env with your secrets (API_KEY, JWT_SECRET, etc.)\"

npm ci
npm run build
cp -r dist/* /var/www/apfa/ || cp -r public/* /var/www/apfa/ || true

cp nginx.conf /etc/nginx/sites-available/apfa
ln -sf /etc/nginx/sites-available/apfa /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx

certbot --nginx \\
  --agree-tos \\
  --email admin@secureai.dev \\
  --domains apfa.secureai.dev \\
  --non-interactive \\
  --redirect

docker compose up -d --build

echo \"✅ Setup complete!\"
echo \"🌐 Frontend: https://apfa.secureai.dev\"
echo \"📊 Grafana: http://67.205.140.55:3001 (admin/admin)\"
echo \"📈 Prometheus: http://67.205.140.55:9090\"
echo \"🗄️  Postgres: localhost:5432 (postgres/password/apfa)\"
echo \"💾 MinIO: http://67.205.140.55:9001 (minioadmin/minioadmin)\"
