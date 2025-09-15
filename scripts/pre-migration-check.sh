#!/bin/bash
# Pre-migration checklist - run BEFORE making model changes

set -e

echo "🔍 Pre-migration safety checklist..."

# 1. Show current migration state
echo "📋 Current migration state:"
python manage.py showmigrations

# 2. Check for pending migrations
echo "📋 Checking for pending migrations..."
if python manage.py makemigrations --check --dry-run 2>&1 | grep -q "No changes detected"; then
    echo "✅ No pending migrations detected"
else
    echo "⚠️  WARNING: Pending migrations detected!"
    echo "Run 'python manage.py makemigrations' to see what would be created"
    echo "Consider committing pending migrations before making new model changes"
fi

# 3. Check current model state vs migrations
echo "📋 Validating current model-migration consistency..."
python manage.py makemigrations --check --dry-run

# 4. Show recent migrations for context
echo "📋 Recent migrations for context:"
find . -name "migrations/*.py" -not -name "__init__.py" -newer $(git log -1 --format="%ai" | head -1) 2>/dev/null | head -10 || echo "No recent migration files found"

# 5. Check if any models have been modified since last migration
echo "📋 Checking for model changes since last commit..."
if git diff --name-only HEAD | grep -E "(models\.py|admin\.py)" | head -5; then
    echo "⚠️  Model files have been modified since last commit"
    echo "Review these changes carefully before creating migrations"
else
    echo "✅ No model file changes detected since last commit"
fi

echo "✅ Pre-migration check completed. Safe to proceed with model changes."