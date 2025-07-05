#!/bin/bash
# This script sets up a cron job to run the publish_scheduled management command every hour

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create a temporary crontab file
TEMP_CRONTAB=$(mktemp)
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# Minimalwave Blog Crontab" > "$TEMP_CRONTAB"

# Check if the cron job already exists
if grep -q "publish_scheduled" "$TEMP_CRONTAB"; then
    echo "Cron job for publish_scheduled already exists"
else
    # Add the cron job to run every hour
    echo "0 * * * * cd $PROJECT_DIR && python manage.py publish_scheduled >> $PROJECT_DIR/logs/scheduled_publishing.log 2>&1" >> "$TEMP_CRONTAB"

    # Create the logs directory if it doesn't exist
    mkdir -p "$PROJECT_DIR/logs"

    # Install the new crontab
    crontab "$TEMP_CRONTAB"
    echo "Cron job added to publish scheduled content every hour"
fi

# Clean up the temporary file
rm "$TEMP_CRONTAB"

echo "Current crontab:"
crontab -l
