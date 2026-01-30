#!/bin/bash
# Check for pending Django migrations

set -e

echo "🔍 Checking for pending Django migrations..."

# Check if docker-compose is running
if ! docker-compose ps | grep -q "Up"; then
    echo "🚀 Starting docker-compose services..."
    docker-compose up -d
    sleep 10
fi

# Check for pending migrations
PENDING=$(docker-compose exec -T web python manage.py showmigrations --plan | grep -c "\[ \]" || true)

if [ "$PENDING" -gt 0 ]; then
    echo "❌ Found $PENDING pending migration(s)!"
    echo "📋 Pending migrations:"
    docker-compose exec -T web python manage.py showmigrations --plan | grep "\[ \]"
    echo ""
    echo "💡 Run: docker-compose exec web python manage.py migrate"
    echo "   or: make migrate"
    exit 1
else
    echo "✅ No pending migrations found"
fi