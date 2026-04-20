#!/bin/bash
set -e

echo "🔧 Setting environment..."
export PATH=$PATH:/home/frappe/.local/bin

# ── Variables ──
SITE="hr-uat.fujishkaerp.com"
BENCH_DIR="/home/frappe/fujishka-bench"
RELEASES_DIR="/home/frappe/releases"
BACKUP_DIR="/home/frappe/backups"
DEPLOY_TMP="/home/frappe/deploy_tmp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RELEASE_DIR="$RELEASES_DIR/release_$TIMESTAMP"
PREVIOUS_APP_BACKUP="$BACKUP_DIR/app_backup_$TIMESTAMP"

echo "🚀 Starting deployment at $TIMESTAMP..."

cd $BENCH_DIR

# ── Step 1: Create release folder ──
echo "📦 Creating release folder..."
mkdir -p $RELEASE_DIR

# ── Step 2: Copy artifact ──
echo "📦 Copying artifact..."
cp -r $DEPLOY_TMP/* $RELEASE_DIR/

# ── Step 3: DB Backup (MANDATORY — stops deploy if fails) ──
echo "💾 Taking DB backup..."
mkdir -p $BACKUP_DIR
if ! bench --site $SITE backup --with-files; then
    echo "❌ Backup failed — stopping deployment for safety!"
    echo "❌ Fix backup issue before deploying."
    exit 1
fi
echo "✅ Backup completed successfully"

# Save latest backup path for auto DB restore if needed
LATEST_BACKUP=$(ls -t $BENCH_DIR/sites/$SITE/private/backups/*.sql.gz 2>/dev/null | head -n 1)
echo "📦 Backup saved at: $LATEST_BACKUP"

# ── Step 4: Backup current app code (for rollback) ──
echo "📦 Backing up current app code..."
mkdir -p $PREVIOUS_APP_BACKUP
cp -r $BENCH_DIR/apps/fujishkahr $PREVIOUS_APP_BACKUP/ || true

# ── Step 5: Deploy new app code ──
echo "🔁 Updating custom app..."
rm -rf $BENCH_DIR/apps/fujishkahr
cp -r $RELEASE_DIR $BENCH_DIR/apps/fujishkahr

# ── Step 6: Init git (required by bench) ──
echo "📦 Initialising git for bench compatibility..."
cd $BENCH_DIR/apps/fujishkahr
git init
git add .
git commit -m "deploy-$TIMESTAMP" --quiet

# ── Step 7: Install fujishkahr only (skip frappe/erpnext/hrms) ──
echo "📦 Installing fujishkahr package only..."
cd $BENCH_DIR
source env/bin/activate
pip install -e apps/fujishkahr --quiet
deactivate

# ── Step 8: Run DB Migration ──
echo "⚙️ Running migrations..."
if ! bench --site $SITE migrate; then
    echo "❌ Migration failed! Starting auto recovery..."

    # ── Rollback Step 1: Restore old app code ──
    echo "🔁 Restoring previous app code..."
    rm -rf $BENCH_DIR/apps/fujishkahr
    cp -r $PREVIOUS_APP_BACKUP/fujishkahr $BENCH_DIR/apps/

    # ── Rollback Step 2: Reinstall old app ──
    echo "📦 Reinstalling previous app package..."
    cd $BENCH_DIR/apps/fujishkahr
    git init
    git add .
    git commit -m "rollback-$TIMESTAMP" --quiet

    cd $BENCH_DIR
    source env/bin/activate
    pip install -e apps/fujishkahr --quiet
    deactivate

    # ── Rollback Step 3: Re-run migration on old code ──
    echo "🔁 Re-running migration on old code..."
    bench --site $SITE migrate || true

    # ── Rollback Step 4: Restart services ──
    echo "🔄 Restarting services..."
    sudo supervisorctl restart all || bench restart || true
    sleep 8

    # ── Rollback Step 5: Health check ──
    echo "🔍 Checking site health after rollback..."
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
      --max-time 15 http://localhost 2>/dev/null || echo "000")
    echo "--- SITE STATUS: $HTTP_STATUS ---"

    # ── Rollback Step 6: If site broken → auto restore DB ──
    if [ "$HTTP_STATUS" != "200" ] && [ "$HTTP_STATUS" != "302" ]; then
        echo "❌ Site broken after rollback — restoring DB automatically..."

        if [ -z "$LATEST_BACKUP" ]; then
            echo "❌ No backup found — manual intervention required!"
            exit 1
        fi

        echo "📦 Restoring DB from: $LATEST_BACKUP"
        bench --site $SITE restore $LATEST_BACKUP --force

        echo "⚙️ Running migration on restored DB..."
        bench --site $SITE migrate || true

        echo "🧹 Clearing cache..."
        bench --site $SITE clear-cache

        echo "🔄 Restarting after DB restore..."
        sudo supervisorctl restart all || bench restart || true

        echo "✅ DB restored automatically — site recovered!"
    else
        echo "✅ Site healthy after rollback — DB restore not needed"
    fi

    echo "❌ Deployment failed. Site running on previous version."
    exit 1
fi

echo "✅ Migration succeeded!"

# ── Step 9: Build fujishkahr assets only ──
# Note: frappe/erpnext/hrms assets are permanent — built once on server
# Only fujishkahr changes on every deploy
echo "🎨 Building fujishkahr assets only..."
if ! NODE_OPTIONS="--max-old-space-size=512" bench build --app fujishkahr; then
    echo "❌ Build failed — check server memory: free -h"
    exit 1
fi
echo "✅ Build completed!"

# ── Step 10: Clear cache ──
echo "🧹 Clearing cache..."
bench --site $SITE clear-cache
bench --site $SITE clear-website-cache

# ── Step 11: Restart services ──
echo "🔄 Restarting services..."
sudo supervisorctl restart all || bench restart || echo "⚠️ Restart warning, continuing..."

# ── Step 12: Clean deploy_tmp ──
echo "🧹 Cleaning deploy_tmp..."
rm -rf $DEPLOY_TMP/*

echo "✅ Deployment completed successfully at $(date +%Y%m%d_%H%M%S)!"