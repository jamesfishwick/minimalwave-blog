#!/bin/bash
set -e

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Repair database state if needed (production deployment fix)
echo "Repairing database state..."
python manage.py repair_database_state || true

# Fix schema alignment issues (column naming mismatches)
echo "Fixing schema alignment..."
python manage.py fix_schema_alignment || true

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Create superuser if DJANGO_SUPERUSER_* environment variables are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" --noinput || true
fi

# Set up cron job for scheduled publishing if in production mode
if [[ "$DJANGO_SETTINGS_MODULE" == *"production"* ]]; then
    # Set up cron job for scheduled publishing
    echo "Setting up cron job for scheduled publishing..."

    # Create cron directory if it doesn't exist
    mkdir -p /etc/cron.d

    # Create the crontab file
    cat > /etc/cron.d/publish-scheduled << EOF
# Run the publish_scheduled command every hour
0 * * * * root cd /app && python manage.py publish_scheduled >> /app/logs/scheduled_publishing.log 2>&1
EOF

    # Give proper permissions to the cron job
    chmod 0644 /etc/cron.d/publish-scheduled

    # Create logs directory
    mkdir -p /app/logs

    echo "Cron job for scheduled publishing has been set up"
fi

# Execute command passed to entrypoint
exec "$@"
