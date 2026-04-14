#!/bin/bash
set -e

echo "🔧 Setting environment..."
export PATH=$PATH:/home/frappe/.local/bin

# Variables
SITE="hr.fujishkaerp.com"
BENCH_DIR="/home/frappe/fujishka-bench"
RELEASES_DIR="/home/frappe/releases"
BACKUP_DIR="/home/frappe/backups"
DEPLOY_TMP="/home/frappe/deploy_tmp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RELEASE_DIR="$RELEASES_DIR/release_$TIMESTAMP"

echo "🚀 Starting deployment..."

# Go to bench
cd $BENCH_DIR

echo "📦 Creating release folder..."
mkdir -p $RELEASE_DIR

echo "📦 Copying new code from artifact..."
cp -r $DEPLOY_TMP/* $RELEASE_DIR/

echo "💾 Taking backup..."
mkdir -p $BACKUP_DIR
bench --site $SITE backup --with-files

echo "🔁 Linking new release..."

# Optional: replace only custom app (recommended)
rm -rf $BENCH_DIR/apps/fujishkahr
cp -r $RELEASE_DIR/fujishkahr $BENCH_DIR/apps/

echo "⚙️ Running migrations..."
bench --site $SITE migrate

echo "🎨 Building assets..."
bench build

echo "🧹 Clearing cache..."
bench --site $SITE clear-cache

echo "🔄 Restarting services..."
bench restart

echo "🧹 Cleaning old releases..."
cd $RELEASES_DIR
ls -1t | grep '^release_' | tail -n +6 | xargs rm -rf || true

echo "🧹 Cleaning old backups..."
cd $BACKUP_DIR
ls -1t | tail -n +6 | xargs rm -rf || true

echo "✅ Deployment completed successfully!"
