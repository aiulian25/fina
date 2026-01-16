#!/bin/bash
# FINA Quick Deploy Script
# Run on any machine with Docker installed

set -e

echo "🚀 FINA Quick Deploy"
echo "===================="

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p data uploads

# Check if logged into GitHub Container Registry
echo "🔐 Checking GitHub Container Registry login..."
if ! docker pull ghcr.io/aiulian25/fina:latest 2>/dev/null; then
    echo ""
    echo "⚠️  Need to login to GitHub Container Registry"
    echo "   Get a token from: https://github.com/settings/tokens"
    echo "   (Select 'read:packages' scope)"
    echo ""
    read -p "Enter your GitHub username: " GITHUB_USER
    read -sp "Enter your GitHub PAT token: " GITHUB_TOKEN
    echo ""
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
    docker pull ghcr.io/aiulian25/fina:latest
fi

# Generate a random SECRET_KEY if not set
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    echo "🔑 Generated SECRET_KEY"
fi

# Create docker-compose.prod.yml if it doesn't exist
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "📝 Creating docker-compose.prod.yml..."
    cat > docker-compose.prod.yml << 'COMPOSE'
services:
  web:
    image: ghcr.io/aiulian25/fina:latest
    container_name: fina
    ports:
      - "5103:5103"
    volumes:
      - ./data:/app/data:rw
      - ./uploads:/app/uploads:rw
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=sqlite:////app/data/fina.db
      - HTTPS_ENABLED=false
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - fina-network

  redis:
    image: redis:7-alpine
    container_name: fina-redis
    restart: unless-stopped
    networks:
      - fina-network
    volumes:
      - redis-data:/data

volumes:
  redis-data:

networks:
  fina-network:
    driver: bridge
COMPOSE
fi

# Create .env file
echo "SECRET_KEY=$SECRET_KEY" > .env

# Start the app
echo "🐳 Starting FINA..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "✅ FINA is running!"
echo "   Access at: http://localhost:5103"
echo ""
echo "📋 Useful commands:"
echo "   View logs:    docker logs -f fina"
echo "   Stop:         docker compose -f docker-compose.prod.yml down"
echo "   Update:       docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d"
