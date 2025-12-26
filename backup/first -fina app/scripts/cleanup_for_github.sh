#!/bin/bash

echo "🧹 Cleaning personal information..."

# Remove personal data and sensitive files
rm -rf instance/
rm -rf backups/
rm -rf __pycache__/
rm -rf app/__pycache__/
rm -rf app/*/__pycache__/
rm -rf .pytest_cache/
rm -rf venv/
rm -rf env/
rm -f *.db
rm -f *.sqlite
rm -f *.sqlite3
rm -f .env
rm -f *.log
rm -f *.tar
rm -f *.tar.gz
rm -f make_admin.py
rm -f test_qr.py
rm -f migrate_db.py
rm -f backup*.sh
rm -f create_deployment_package.sh

# Remove uploaded files
rm -rf app/static/uploads/*
touch app/static/uploads/.gitkeep

echo "✅ Cleanup complete!"
