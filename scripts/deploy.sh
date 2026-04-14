#!/bin/bash
set -e

echo "🔧 Setting environment..."
export PATH=$PATH:/home/frappe/.local/bin

# Variables
SITE="hr-uat.fujishkaerp.com"
BENCH_DIR="/home/frappe/fujishka-bench"
RELEASES_DIR="/home/frappe/releases"
BACKUP_DIR="/home/frappe/backups"
DEPLOY_TMP="/home/frappe/deploy_tmp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RELEASE_DIR="$RELEASES_DIR/release_$TIMESTAMP"
APP_BACKUP_DIR="$BACKUP_DIR/app_backup_$TIMESTAMP"

echo "🚀 Starting deployment..."

cd $BENCH_DIR

echo "🔧 Enabling maintenance mode..."
bench --site $SITE set-maintenance-mode on || true

echo "📦 Creating release folder..."
mkdir -p $RELEASE_DIR

echo "📦 Copying artifact..."
cp -r $DEPLOY_TMP/* $RELEASE_DIR/

echo "💾 Taking full backup (DB + files)..."
mkdir -p $BACKUP_DIR
bench --site $SITE backup --with-files || echo "⚠️ Backup failed, continuing..."

echo "📦 Backing up current app..."
mkdir -p $APP_BACKUP_DIR
cp -r $BENCH_DIR/apps/fujishkahr $APP_BACKUP_DIR/ || true

echo "🔁 Updating custom app..."
rm -rf $BENCH_DIR/apps/fujishkahr
cp -r $RELEASE_DIR/fujishkahr $BENCH_DIR/apps/

echo "📦 Installing requirements..."
bench setup requirements

echo "⚙️ Running migrations..."

if ! bench --site $SITE migrate; then
    echo "❌ Migration failed! Starting rollback..."

    echo "🔁 Restoring previous app..."
    rm -rf $BENCH_DIR/apps/fujishkahr
    cp -r $APP_BACKUP_DIR/fujishkahr $BENCH_DIR/apps/ || true

    echo "📦 Re-installing old dependencies..."
    bench setup requirements

    echo "🔁 Reverting DB (Restoring from latest backup)..."

    LATEST_DB_BACKUP=$(ls -t $BACKUP_DIR/*-database.sql.gz | head -1)
    LATEST_PUBLIC_FILES=$(ls -t $BACKUP_DIR/*-files.tar | head -1)
    LATEST_PRIVATE_FILES=$(ls -t $BACKUP_DIR/*-private-files.tar | head -1)

    if [ -n "$LATEST_DB_BACKUP" ]; then
        echo "📦 Restoring database and files..."

        bench --site $SITE --force restore $LATEST_DB_BACKUP \
            --with-public-files $LATEST_PUBLIC_FILES \
            --with-private-files $LATEST_PRIVATE_FILES

        echo "🔄 Running migrate after restore..."
        bench --site $SITE migrate || true
    else
        echo "⚠️ No database backup found to restore!"
    fi

    echo "🔧 Disabling maintenance mode..."
    bench --site $SITE set-maintenance-mode off || true

    echo "❌ Deployment failed and rolled back!"
    exit 1
fi

echo "🎨 Building assets..."
bench build

echo "🧹 Clearing cache..."
bench --site $SITE clear-cache

echo "🔄 Restarting services..."
bench restart

echo "🔧 Disabling maintenance mode..."
bench --site $SITE set-maintenance-mode off || true

echo "🧹 Cleaning old releases..."
cd $RELEASES_DIR
ls -1t | grep '^release_' | tail -n +6 | xargs rm -rf || true

echo "🧹 Cleaning old backups..."
cd $BACKUP_DIR
ls -1t | tail -n +6 | xargs rm -rf || true

echo "✅ Deployment completed successfully!"
