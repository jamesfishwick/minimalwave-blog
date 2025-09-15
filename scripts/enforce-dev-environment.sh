#!/bin/bash
# Enforce development environment usage to prevent sync issues

set -e

echo "🔍 Checking Docker Compose environment..."

# Check if using development environment
if docker-compose ps | grep -q "minimalwave-blog-container"; then
    # Check if source code is mounted
    if docker-compose exec web test -f /app/manage.py 2>/dev/null && \
       docker-compose exec web test -d /app/blog 2>/dev/null; then
        
        # Check if changes sync both ways
        echo "📋 Testing bidirectional sync..."
        
        # Create a test file locally
        echo "test" > /tmp/sync_test_local
        
        # Copy to container and check if it appears locally
        docker-compose exec web touch /app/sync_test_container
        
        if [ -f "./sync_test_container" ]; then
            echo "✅ Source code is properly mounted and synced"
            rm -f /tmp/sync_test_local ./sync_test_container
            docker-compose exec web rm -f /app/sync_test_container
        else
            echo "❌ CRITICAL: Source code not synced!"
            echo "You're using production Docker setup for development."
            echo ""
            echo "SOLUTION: Use development environment:"
            echo "  docker-compose down"
            echo "  docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d"
            echo "  # OR use the Makefile:"
            echo "  make dev"
            exit 1
        fi
    else
        echo "❌ CRITICAL: Source code not available in container!"
        echo "Using wrong Docker configuration."
        exit 1
    fi
else
    echo "ℹ️  No containers running. Start with development environment:"
    echo "  make dev"
fi