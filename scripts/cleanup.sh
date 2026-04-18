#!/bin/bash

echo "🧹 Cleaning old releases..."
cd /home/frappe/releases
ls -1t | grep '^release_' | tail -n +6 | xargs rm -rf 2>/dev/null || true

echo "🧹 Cleaning old backups..."
cd /home/frappe/fujishka-bench/sites/hr-uat.fujishkaerp.com/private/backups
ls -1t *.sql.gz | tail -n +6 | xargs rm -f 2>/dev/null || true

echo "✅ Cleanup done"
