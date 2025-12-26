#!/bin/bash

# Database Migration Script for Smart Features
# This script adds the necessary tables for subscription tracking

echo "🔄 Migrating database for Smart Features..."

# Backup existing database
echo "📦 Creating backup..."
docker run --rm -v fina-db:/data -v $(pwd):/backup alpine cp /data/finance.db /backup/finance_backup_$(date +%Y%m%d_%H%M%S).db

echo "✅ Backup created"

# Stop containers
echo "🛑 Stopping containers..."
docker compose down

# Rebuild with new dependencies
echo "🏗️ Rebuilding containers..."
docker compose build

# Start containers (migrations will run automatically)
echo "🚀 Starting containers..."
docker compose up -d

echo ""
echo "✅ Migration complete!"
echo ""
echo "New features available:"
echo "  • Smart recurring expense detection"
echo "  • Subscription management"
echo "  • Multi-language support (EN, RO, ES)"
echo "  • PWA support"
echo ""
echo "Access your app at: http://localhost:5001"
echo "Navigate to Subscriptions to start tracking!"
