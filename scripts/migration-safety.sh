#!/bin/bash
# Unified migration safety operations
# Consolidates: validate-migrations.sh, validate-migration-dependencies.sh,
#               test-migrations-clean.sh, check-migrations.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  --pre-check      Pre-flight checklist BEFORE making model changes"
    echo "  --validate       Validate migration dependencies and consistency"
    echo "  --test-clean     Test migrations in clean environment"
    echo "  --check-pending  Check for pending migrations"
    echo "  --all            Run all safety checks (default)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --pre-check          # Before modifying models"
    echo "  $0 --validate           # Quick validation"
    echo "  $0 --test-clean         # Full clean environment test"
    echo "  $0 --all                # Complete safety check"
}

ensure_docker_running() {
    if ! docker-compose ps | grep -q "Up"; then
        echo -e "${BLUE}🚀 Starting docker-compose services...${NC}"
        cd "$PROJECT_ROOT/deploy/docker" && docker-compose up -d
        sleep 10
    fi
}

validate_migrations() {
    echo -e "${BLUE}🔍 Validating Django migration dependencies...${NC}"

    ensure_docker_running

    # Use Django management command for thorough validation
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py validate_migrations

    # Check for pending migrations
    echo -e "${BLUE}📋 Checking for uncommitted migrations...${NC}"
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py makemigrations --check --dry-run

    # Check for migration conflicts
    echo -e "${BLUE}🔍 Checking for migration conflicts...${NC}"
    if cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py showmigrations 2>&1 | grep -q "conflicting migrations"; then
        echo -e "${RED}❌ Migration conflicts detected!${NC}"
        cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py showmigrations
        exit 1
    fi

    echo -e "${GREEN}✅ Migration validation completed${NC}"
}

test_clean_environment() {
    echo -e "${BLUE}🧪 Testing migrations in clean environment...${NC}"

    # Create backup
    BACKUP_FILE="$PROJECT_ROOT/data/db-backup-$(date +%Y%m%d-%H%M%S).sqlite3"
    if [ -f "$PROJECT_ROOT/data/db.sqlite3" ]; then
        echo -e "${YELLOW}💾 Backing up current database...${NC}"
        cp "$PROJECT_ROOT/data/db.sqlite3" "$BACKUP_FILE"
        echo -e "${GREEN}✅ Database backed up to: $BACKUP_FILE${NC}"
    fi

    # Clean environment
    echo -e "${YELLOW}🗑️  Cleaning up containers and volumes...${NC}"
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose down -v

    # Start fresh
    echo -e "${BLUE}🚀 Starting fresh containers...${NC}"
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose up -d
    sleep 15

    # Run migrations
    echo -e "${BLUE}🔄 Running migrations from scratch...${NC}"
    if ! cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py migrate; then
        echo -e "${RED}❌ Migration failed in clean environment!${NC}"
        if [ -f "$BACKUP_FILE" ]; then
            echo -e "${YELLOW}🔧 Restoring from backup...${NC}"
            cd "$PROJECT_ROOT/deploy/docker" && docker-compose down
            cp "$BACKUP_FILE" "$PROJECT_ROOT/data/db.sqlite3"
            cd "$PROJECT_ROOT/deploy/docker" && docker-compose up -d
        fi
        exit 1
    fi

    # Smoke test
    echo -e "${BLUE}🧪 Running Django system check...${NC}"
    if ! cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py check; then
        echo -e "${RED}❌ Django check failed after migration!${NC}"
        exit 1
    fi

    # Cleanup backup
    if [ -f "$BACKUP_FILE" ]; then
        rm "$BACKUP_FILE"
        echo -e "${YELLOW}🗑️  Cleaned up backup file${NC}"
    fi

    echo -e "${GREEN}✅ Migrations tested successfully in clean environment!${NC}"
}

check_pending() {
    echo -e "${BLUE}📋 Checking for pending migrations...${NC}"

    ensure_docker_running

    if cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py makemigrations --check --dry-run 2>&1 | grep -q "No changes detected"; then
        echo -e "${GREEN}✅ No pending migrations detected${NC}"
    else
        echo -e "${YELLOW}⚠️  WARNING: Pending migrations detected!${NC}"
        echo -e "${YELLOW}Run 'make makemigrations' to create them${NC}"
        exit 1
    fi
}

pre_check() {
    echo -e "${BLUE}🔍 Pre-migration safety checklist...${NC}"
    echo ""

    ensure_docker_running

    # 1. Show current migration state
    echo -e "${BLUE}📋 Current migration state:${NC}"
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py showmigrations
    echo ""

    # 2. Check for pending migrations
    echo -e "${BLUE}📋 Checking for pending migrations...${NC}"
    if cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T web python manage.py makemigrations --check --dry-run 2>&1 | grep -q "No changes detected"; then
        echo -e "${GREEN}✅ No pending migrations detected${NC}"
    else
        echo -e "${YELLOW}⚠️  WARNING: Pending migrations detected!${NC}"
        echo -e "${YELLOW}Run 'python manage.py makemigrations' to see what would be created${NC}"
        echo -e "${YELLOW}Consider committing pending migrations before making new model changes${NC}"
    fi
    echo ""

    # 3. Check if any models have been modified since last commit
    echo -e "${BLUE}📋 Checking for model changes since last commit...${NC}"
    cd "$PROJECT_ROOT"
    if git diff --name-only HEAD | grep -E "(models\.py|admin\.py)" | head -5; then
        echo -e "${YELLOW}⚠️  Model files have been modified since last commit${NC}"
        echo -e "${YELLOW}Review these changes carefully before creating migrations${NC}"
    else
        echo -e "${GREEN}✅ No model file changes detected since last commit${NC}"
    fi
    echo ""

    # 4. Show recent migrations for context
    echo -e "${BLUE}📋 Recent migration files:${NC}"
    find "$PROJECT_ROOT" -path "*/migrations/*.py" -not -name "__init__.py" -mtime -7 2>/dev/null | head -10 || echo "No recent migration files found"
    echo ""

    echo -e "${GREEN}✅ Pre-migration check completed. Safe to proceed with model changes.${NC}"
}

run_all() {
    echo -e "${BLUE}🛡️  Running complete migration safety check...${NC}"
    echo ""

    validate_migrations
    echo ""

    check_pending
    echo ""

    test_clean_environment
    echo ""

    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✅ All migration safety checks passed!${NC}"
    echo -e "${GREEN}================================${NC}"
}

# Main
MODE="${1:---all}"

case "$MODE" in
    --pre-check)
        pre_check
        ;;
    --validate)
        validate_migrations
        ;;
    --test-clean)
        test_clean_environment
        ;;
    --check-pending)
        check_pending
        ;;
    --all)
        run_all
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
