#!/bin/bash
# Scheduled publishing operations
# Merges: setup_scheduled_publishing.sh, test_scheduling.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  --setup     Set up cron job for scheduled publishing"
    echo "  --test      Create test scheduled content"
    echo "  --run       Run publish_scheduled command"
    echo "  --help      Show this help message"
}

setup_cron() {
    echo -e "${BLUE}Setting up scheduled publishing cron job...${NC}"

    TEMP_CRONTAB=$(mktemp)
    crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# Minimalwave Blog Crontab" > "$TEMP_CRONTAB"

    if grep -q "publish_scheduled" "$TEMP_CRONTAB"; then
        echo -e "${GREEN}✅ Cron job already exists${NC}"
    else
        echo "0 * * * * cd $PROJECT_ROOT && python manage.py publish_scheduled >> $PROJECT_ROOT/logs/scheduled_publishing.log 2>&1" >> "$TEMP_CRONTAB"
        mkdir -p "$PROJECT_ROOT/logs"
        crontab "$TEMP_CRONTAB"
        echo -e "${GREEN}✅ Cron job added to run every hour${NC}"
    fi

    rm "$TEMP_CRONTAB"

    echo ""
    echo "Current crontab:"
    crontab -l
}

test_scheduling() {
    echo -e "${BLUE}Creating test scheduled content...${NC}"

    python "$PROJECT_ROOT/manage.py" shell << EOF
from blog.models import Entry
from til.models import TIL
from datetime import datetime, timedelta
from django.utils import timezone

# Create scheduled blog entry
future_time = timezone.now() + timedelta(hours=1)
entry = Entry.objects.create(
    title="Test Scheduled Entry",
    summary="This entry is scheduled for future publication",
    body="# Test Content\n\nThis will be published in 1 hour.",
    status="draft",
    publish_date=future_time
)
print(f"Created Entry: {entry.title} scheduled for {future_time}")

# Create scheduled TIL
til = TIL.objects.create(
    title="Test Scheduled TIL",
    content="This TIL will publish in 1 hour",
    status="draft",
    publish_date=future_time
)
print(f"Created TIL: {til.title} scheduled for {future_time}")

print("\nTo publish now, run:")
print("  python manage.py publish_scheduled")
EOF

    echo -e "${GREEN}✅ Test content created${NC}"
}

run_publishing() {
    echo -e "${BLUE}Running scheduled publishing...${NC}"

    python "$PROJECT_ROOT/manage.py" publish_scheduled

    echo -e "${GREEN}✅ Publishing complete${NC}"
}

# Main
MODE="${1:---help}"

case "$MODE" in
    --setup)
        setup_cron
        ;;
    --test)
        test_scheduling
        ;;
    --run)
        run_publishing
        ;;
    --help)
        usage
        exit 0
        ;;
    *)
        echo -e "${RED}Error: Unknown mode '$MODE'${NC}"
        echo ""
        usage
        exit 1
        ;;
esac
