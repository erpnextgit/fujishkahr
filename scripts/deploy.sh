#!/bin/bash
set -e

echo "🚀 Starting deployment..."

APP_DIR="/home/frappe/fujishka-bench"
RELEASE_DIR="/home/frappe/releases/release_$(date +%Y%m%d%H%M%S)"

mkdir -p $RELEASE_DIR

echo "📦 Copying app..."
cp -r /home/frappe/deploy_tmp/fujishkahr $RELEASE_DIR/

echo "💾 Backup..."
cd $APP_DIR
bench --site hr.fujishkaerp.com backup

echo "⬇️ Updating app..."
bench get-app $RELEASE_DIR/fujishkahr --overwrite

echo "🔄 Migrate..."
bench --site hr.fujishkaerp.com migrate

echo "🏗️ Build..."
bench build

echo "🔁 Restart..."
bench restart

echo "✅ Deployment done"
