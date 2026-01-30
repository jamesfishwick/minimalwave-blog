#!/bin/bash
# Validate Django migration dependencies and detect common issues

set -e

echo "🔍 Validating Django migration dependencies..."

# Check if docker-compose is running
if ! docker-compose ps | grep -q "Up"; then
    echo "🚀 Starting docker-compose services..."
    docker-compose up -d
    sleep 10
fi

# Validate migrations don't have issues
echo "📋 Running Django migration checks..."
docker-compose exec -T web python manage.py makemigrations --check --dry-run

# Check for potential migration conflicts
echo "🔍 Checking for migration conflicts..."
if docker-compose exec -T web python manage.py showmigrations 2>&1 | grep -q "conflicting migrations"; then
    echo "❌ Migration conflicts detected!"
    docker-compose exec -T web python manage.py showmigrations
    exit 1
fi

# Look for fake or empty migrations in new changes
echo "🔍 Checking for fake/empty migrations..."
for migration_file in $(find . -name "migrations/*.py" -newer .git/HEAD 2>/dev/null || true); do
    if grep -q "operations = \[\]" "$migration_file" 2>/dev/null; then
        echo "⚠️  Warning: Empty migration found: $migration_file"
        echo "   Empty migrations can cause issues in CI/CD environments"
    fi
done

echo "✅ Migration validation completed"