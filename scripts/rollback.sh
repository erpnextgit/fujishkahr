#!/bin/bash
set -e

echo "⏪ Rolling back..."

APP_DIR="/home/frappe/fujishka-bench"
BACKUP=$(ls -t /home/frappe/backups/*sql.gz | head -n 1)

cd $APP_DIR

bench --site hr.fujishkaerp.com restore $BACKUP --force
bench migrate
bench restart

echo "✅ Rollback complete"
