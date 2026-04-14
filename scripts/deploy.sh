#!/bin/bash
set -e

echo "🔧 Setting environment..."
export PATH=$PATH:/home/frappe/.local/bin

# Variables
#var
SITE="hr-uat.fujishkaerp.com"
BENCH_DIR="/home/frappe/fujishka-bench"
RELEASES_DIR="/home/frappe/releases"
BACKUP_DIR="/home/frappe/backups"
DEPLOY_TMP="/home/frappe/deploy_tmp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RELEASE_DIR="$RELEASES_DIR/release_$TIMESTAMP"
PREVIOUS_APP_BACKUP="/home/frappe/backups/app_backup_$TIMESTAMP"

echo "🚀 Starting deployment..."

cd $BENCH_DIR

echo "📦 Creating release folder..."
mkdir -p $RELEASE_DIR

echo "📦 Copying artifact..."
cp -r $DEPLOY_TMP/* $RELEASE_DIR/

echo "💾 Taking DB backup..."
mkdir -p $BACKUP_DIR
bench --site $SITE backup --with-files || echo "⚠️ Backup failed, continuing..."

echo "📦 Backing up current app (for rollback)..."
mkdir -p $PREVIOUS_APP_BACKUP
cp -r $BENCH_DIR/apps/fujishkahr $PREVIOUS_APP_BACKUP/ || true

echo "🔁 Updating custom app..."

rm -rf $BENCH_DIR/apps/fujishkahr
cp -r $RELEASE_DIR/fujishkahr $BENCH_DIR/apps/

echo "📦 Installing requirements (IMPORTANT FIX)..."
bench setup requirements

echo "⚙️ Running migrations..."
if ! bench --site $SITE migrate; then
    echo "❌ Migration failed! Rolling back app..."

    rm -rf $BENCH_DIR/apps/fujishkahr
    cp -r $PREVIOUS_APP_BACKUP/fujishkahr $BENCH_DIR/apps/

    echo "🔄 Re-installing old dependencies..."
    bench setup requirements

    echo "🔁 Reverting DB (manual restore may be needed)"
    bench --site $SITE migrate || true

    echo "❌ Rollback completed. Exiting..."
    exit 1
fi

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
