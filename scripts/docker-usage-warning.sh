#!/bin/bash
# Warn about Docker Compose usage patterns

echo "⚠️  WARNING: You're using basic docker-compose commands."
echo ""
echo "For DEVELOPMENT (with migration file sync):"
echo "  make dev                    # Starts with source code mounting"
echo "  make makemigrations         # Safe migration creation"
echo ""
echo "For PRODUCTION:"
echo "  make prod                   # Production environment"
echo ""
echo "❌ DON'T use 'docker-compose up' directly for development"
echo "✅ USE 'make dev' to ensure proper file synchronization"
echo ""
read -p "Continue anyway? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborting. Use 'make dev' instead."
    exit 1
fi