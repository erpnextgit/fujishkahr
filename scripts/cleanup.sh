#!/bin/bash

echo "🧹 Cleaning releases..."
cd /home/frappe/releases
ls -1t | grep '^release_' | tail -n +6 | xargs rm -rf

echo "🧹 Cleaning backups..."
cd /home/frappe/backups
ls -1t | tail -n +6 | xargs rm -f

echo "✅ Cleanup done"
