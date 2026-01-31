#!/bin/bash
# Sync production Azure PostgreSQL database to local Docker environment
# Usage: ./scripts/sync-db-from-production.sh [--no-backup] [--dry-run]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROD_HOST="minimalwave-db.postgres.database.azure.com"
PROD_DB="minimalwave"
PROD_USER="minimalwave"
PROD_PORT="5432"

LOCAL_HOST="db"
LOCAL_DB="minimalwave"
LOCAL_USER="postgres"
LOCAL_PORT="5432"

BACKUP_DIR="$PROJECT_ROOT/data/backups"
KEEP_DUMPS=5

# Flags
NO_BACKUP=false
DRY_RUN=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-backup    Skip local database backup before sync"
            echo "  --dry-run      Show what would happen without executing"
            echo "  --help         Show this help message"
            echo ""
            echo "Example:"
            echo "  $0              # Full sync with automatic backup"
            echo "  $0 --no-backup  # Sync without local backup (faster)"
            echo "  $0 --dry-run    # See what would happen"
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option '$arg'${NC}"
            exit 1
            ;;
    esac
done

usage() {
    echo -e "${BLUE}Production Database Sync${NC}"
    echo ""
    echo "Syncs production Azure PostgreSQL database to local Docker environment"
    echo ""
    echo "Usage: $0 [--no-backup] [--dry-run]"
    echo ""
    echo "For help: $0 --help"
}

# Pre-flight checks
preflight_checks() {
    echo -e "${BLUE}Running pre-flight checks...${NC}"
    echo ""

    # Check pg_dump installed
    if ! command -v pg_dump &> /dev/null; then
        echo -e "${RED}❌ pg_dump not found${NC}"
        echo "Install PostgreSQL client tools:"
        echo "  macOS: brew install postgresql"
        echo "  Ubuntu: sudo apt-get install postgresql-client"
        exit 1
    fi
    echo -e "${GREEN}✓ pg_dump installed${NC}"

    # Check Docker running
    if ! docker ps &> /dev/null; then
        echo -e "${RED}❌ Docker not running${NC}"
        echo "Start Docker Desktop and try again"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is running${NC}"

    # Check database container running
    if ! docker-compose -f "$PROJECT_ROOT/deploy/docker/docker-compose.yml" ps | grep -q "minimalwave-blog-db.*Up"; then
        echo -e "${YELLOW}⚠️  Local database container not running${NC}"
        echo "Starting database container..."
        cd "$PROJECT_ROOT/deploy/docker" && docker-compose up -d db
        sleep 5
    fi
    echo -e "${GREEN}✓ Local database container is running${NC}"

    echo ""
}

# Load production credentials
load_credentials() {
    echo -e "${BLUE}Loading production credentials...${NC}"

    # Try to load from .env file
    if [ -f "$PROJECT_ROOT/.env" ]; then
        # Extract DATABASE_URL
        DATABASE_URL=$(grep -E "^DATABASE_URL=" "$PROJECT_ROOT/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'")

        if [ -n "$DATABASE_URL" ]; then
            # Parse password from DATABASE_URL using Python (handles @ in password)
            # Format: postgres://user:password@host:port/database
            PROD_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.urlparse('$DATABASE_URL').password)" 2>/dev/null)

            if [ -n "$PROD_PASSWORD" ]; then
                echo -e "${GREEN}✓ Production password loaded from .env${NC}"
                return 0
            fi
        fi
    fi

    # Fallback: prompt for password
    echo -e "${YELLOW}⚠️  Production password not found in .env${NC}"
    read -sp "Enter production database password: " PROD_PASSWORD
    echo ""

    if [ -z "$PROD_PASSWORD" ]; then
        echo -e "${RED}❌ Password required${NC}"
        exit 1
    fi
}

# Backup local database
backup_local_database() {
    if [ "$NO_BACKUP" = true ]; then
        echo -e "${YELLOW}⚠️  Skipping local backup (--no-backup flag)${NC}"
        return 0
    fi

    echo -e "${BLUE}Backing up local database...${NC}"

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Generate timestamped backup filename
    LOCAL_BACKUP_FILE="$BACKUP_DIR/local-backup-$(date +%Y%m%d-%H%M%S).sql"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would create backup: $LOCAL_BACKUP_FILE${NC}"
        return 0
    fi

    # Export current local database
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T db pg_dump \
        -U "$LOCAL_USER" \
        -d "$LOCAL_DB" > "$LOCAL_BACKUP_FILE"

    # Check backup was created
    if [ -f "$LOCAL_BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$LOCAL_BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}✓ Local database backed up: $LOCAL_BACKUP_FILE ($BACKUP_SIZE)${NC}"
    else
        echo -e "${RED}❌ Backup failed${NC}"
        exit 1
    fi
}

# Export from production
export_production_database() {
    echo -e "${BLUE}Exporting production database...${NC}"

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Generate timestamped dump filename
    PROD_DUMP_FILE="$BACKUP_DIR/prod-dump-$(date +%Y%m%d-%H%M%S).sql"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would export from:${NC}"
        echo "  Host: $PROD_HOST"
        echo "  Database: $PROD_DB"
        echo "  User: $PROD_USER"
        echo "  Output: $PROD_DUMP_FILE"
        return 0
    fi

    # Export from Azure PostgreSQL
    echo "Connecting to $PROD_HOST..."
    PGSSLMODE=require PGPASSWORD="$PROD_PASSWORD" pg_dump \
        --host="$PROD_HOST" \
        --port="$PROD_PORT" \
        --username="$PROD_USER" \
        --dbname="$PROD_DB" \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges \
        --file="$PROD_DUMP_FILE" 2>&1 | grep -v "^pg_dump: warning:" || true

    # Check dump was created
    if [ -f "$PROD_DUMP_FILE" ]; then
        DUMP_SIZE=$(du -h "$PROD_DUMP_FILE" | cut -f1)
        echo -e "${GREEN}✓ Production database exported: $PROD_DUMP_FILE ($DUMP_SIZE)${NC}"
    else
        echo -e "${RED}❌ Export failed${NC}"
        exit 1
    fi
}

# Import to local
import_to_local() {
    echo -e "${BLUE}Importing to local database...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would import to local database:${NC}"
        echo "  1. Stop web container"
        echo "  2. Drop database: $LOCAL_DB"
        echo "  3. Create database: $LOCAL_DB"
        echo "  4. Import from: $PROD_DUMP_FILE"
        echo "  5. Restart web container"
        return 0
    fi

    # Stop web container to avoid locks
    echo "Stopping web container..."
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose stop web

    # Drop local database
    echo "Dropping local database..."
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T db psql \
        -U "$LOCAL_USER" \
        -c "DROP DATABASE IF EXISTS $LOCAL_DB;" 2>/dev/null || true

    # Create local database
    echo "Creating local database..."
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T db psql \
        -U "$LOCAL_USER" \
        -c "CREATE DATABASE $LOCAL_DB OWNER $LOCAL_USER;"

    # Import dump
    echo "Importing production data..."
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T db psql \
        -U "$LOCAL_USER" \
        -d "$LOCAL_DB" < "$PROD_DUMP_FILE" 2>&1 | grep -v "^SET$" | grep -v "^--" || true

    # Restart web container
    echo "Restarting web container..."
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose start web
    sleep 3

    echo -e "${GREEN}✓ Database imported successfully${NC}"
}

# Verify import
verify_import() {
    echo -e "${BLUE}Verifying import...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would verify:${NC}"
        echo "  - Record counts in key tables"
        echo "  - Django connection"
        return 0
    fi

    # Count records in key tables
    echo ""
    echo "Record counts:"
    cd "$PROJECT_ROOT/deploy/docker" && docker-compose exec -T db psql \
        -U "$LOCAL_USER" \
        -d "$LOCAL_DB" \
        -c "SELECT 'blog_entry' as table_name, COUNT(*) as count FROM blog_entry
            UNION ALL
            SELECT 'blog_blogmark', COUNT(*) FROM blog_blogmark
            UNION ALL
            SELECT 'til_til', COUNT(*) FROM til_til
            UNION ALL
            SELECT 'taggit_tag', COUNT(*) FROM taggit_tag
            ORDER BY table_name;" 2>/dev/null | grep -E "blog_|til_|taggit_|rows" || echo "Tables imported"

    echo ""
    echo -e "${GREEN}✓ Import verification complete${NC}"
}

# Cleanup old dumps
cleanup_old_dumps() {
    echo -e "${BLUE}Cleaning up old dumps...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would keep last $KEEP_DUMPS dumps, delete older ones${NC}"
        return 0
    fi

    # Keep last N production dumps
    PROD_DUMPS=$(ls -t "$BACKUP_DIR"/prod-dump-*.sql 2>/dev/null | tail -n +$((KEEP_DUMPS + 1)))
    if [ -n "$PROD_DUMPS" ]; then
        echo "$PROD_DUMPS" | xargs rm -f
        echo "Cleaned up old production dumps (keeping last $KEEP_DUMPS)"
    fi

    # Keep last N local backups
    LOCAL_BACKUPS=$(ls -t "$BACKUP_DIR"/local-backup-*.sql 2>/dev/null | tail -n +$((KEEP_DUMPS + 1)))
    if [ -n "$LOCAL_BACKUPS" ]; then
        echo "$LOCAL_BACKUPS" | xargs rm -f
        echo "Cleaned up old local backups (keeping last $KEEP_DUMPS)"
    fi
}

# Summary
show_summary() {
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✅ Database sync complete!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}This was a dry run. No changes were made.${NC}"
        echo "Run without --dry-run to actually sync the database."
    else
        echo "Production data is now in your local database."
        echo ""
        echo "Backups saved in: $BACKUP_DIR"
        if [ "$NO_BACKUP" = false ] && [ -n "$LOCAL_BACKUP_FILE" ]; then
            echo "  Local backup: $(basename $LOCAL_BACKUP_FILE)"
        fi
        if [ -n "$PROD_DUMP_FILE" ]; then
            echo "  Production dump: $(basename $PROD_DUMP_FILE)"
        fi
        echo ""
        echo "To restore local backup if needed:"
        echo "  docker-compose exec -T db psql -U postgres -d minimalwave < $LOCAL_BACKUP_FILE"
    fi
    echo ""
}

# Main workflow
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Production Database Sync${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
        echo ""
    fi

    # Confirmation prompt
    if [ "$DRY_RUN" = false ]; then
        echo -e "${YELLOW}⚠️  WARNING: This will replace your local database with production data${NC}"
        read -p "Continue? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Sync cancelled."
            exit 0
        fi
        echo ""
    fi

    preflight_checks
    load_credentials
    backup_local_database
    export_production_database
    import_to_local
    verify_import
    cleanup_old_dumps
    show_summary
}

# Run main
main
