#!/bin/bash
set -e

echo "💾 Taking DB backup before deployment..."

export PATH=$PATH:/home/frappe/.local/bin

SITE="hr-uat.fujishkaerp.com"
BENCH_DIR="/home/frappe/fujishka-bench"

cd $BENCH_DIR

bench --site $SITE backup --with-files

echo "✅ Backup completed successfullyy"
