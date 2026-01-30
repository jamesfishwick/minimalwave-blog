#!/bin/bash
# Test migrations in a clean environment (like CI/CD)

set -e

echo "🧪 Testing migrations in clean environment..."

# Create a backup of current data
echo "💾 Backing up current database..."
BACKUP_FILE="data/db-backup-$(date +%Y%m%d-%H%M%S).sqlite3"
if [ -f "data/db.sqlite3" ]; then
    cp data/db.sqlite3 "$BACKUP_FILE"
    echo "✅ Database backed up to: $BACKUP_FILE"
fi

# Stop containers and remove volumes to simulate clean environment
echo "🗑️  Cleaning up containers and volumes..."
docker-compose down -v

# Start fresh containers
echo "🚀 Starting fresh containers..."
docker-compose up -d
sleep 15

# Run migrations from scratch
echo "🔄 Running migrations from scratch..."
if ! docker-compose exec -T web python manage.py migrate; then
    echo "❌ Migration failed in clean environment!"
    echo "🔧 Restoring from backup..."
    if [ -f "$BACKUP_FILE" ]; then
        docker-compose down
        cp "$BACKUP_FILE" data/db.sqlite3
        docker-compose up -d
    fi
    exit 1
fi

# Run a quick test to make sure everything works
echo "🧪 Running quick smoke test..."
if ! docker-compose exec -T web python manage.py check; then
    echo "❌ Django check failed after migration!"
    exit 1
fi

# Clean up backup if everything succeeded
if [ -f "$BACKUP_FILE" ]; then
    rm "$BACKUP_FILE"
    echo "🗑️  Cleaned up backup file"
fi

echo "✅ Migrations tested successfully in clean environment!"