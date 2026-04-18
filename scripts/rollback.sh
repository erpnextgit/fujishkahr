#!/bin/bash
set -e

echo "⏪ Rolling back..."

export PATH=$PATH:/home/frappe/.local/bin

SITE="hr-uat.fujishkaerp.com"
BENCH_DIR="/home/frappe/fujishka-bench"
BACKUP=$(ls -t /home/frappe/fujishka-bench/sites/$SITE/private/backups/*.sql.gz | head -n 1)

if [ -z "$BACKUP" ]; then
    echo "❌ No backup found! Cannot rollback."
    exit 1
fi

echo "📦 Restoring backup: $BACKUP"

cd $BENCH_DIR

bench --site $SITE restore $BACKUP --force
bench --site $SITE migrate
bench --site $SITE clear-cache
bench restart

echo "✅ Rollback complete"
