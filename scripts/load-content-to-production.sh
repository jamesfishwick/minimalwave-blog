#!/bin/bash
# Promote locally-edited blog content to the PRODUCTION database.
#
# Counterpart to sync-db-from-production.sh (which pulls prod -> local). This
# pushes the markdown content fields (Entry/Blogmark/Project) edited locally via
# dump_content back to production through the Django ORM, so Model.save(),
# status/is_draft sync, and the auto-tag signal all fire (raw SQL skips them).
#
# Usage:
#   ./scripts/load-content-to-production.sh [--all] [--no-backup] [--yes] [content/file.md ...]
#
# Reads DATABASE_URL + SECRET_KEY from .env, snapshots current prod content,
# runs a mandatory dry-run, then (after confirmation) writes with production
# settings. The secrets are passed to the container by env-var NAME only, so
# they never appear in a printed command line.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONTAINER="${CONTENT_CONTAINER:-minimalwave-blog-container}"
SETTINGS="minimalwave-blog.settings.production"
BACKUP_DIR="data/content-backups"

ALL=false
NO_BACKUP=false
ASSUME_YES=false
DRY_ONLY=false
FILES=()

for arg in "$@"; do
    case "$arg" in
        --all)       ALL=true ;;
        --no-backup) NO_BACKUP=true ;;
        --yes|-y)    ASSUME_YES=true ;;
        --dry-run)   DRY_ONLY=true ;;
        --help|-h)
            echo "Usage: $0 [--all] [--no-backup] [--yes] [--dry-run] [content/file.md ...]"
            echo ""
            echo "Promote locally-edited blog content to the PRODUCTION database."
            echo ""
            echo "Options:"
            echo "  --all         Promote every *.md in content/ (else list files explicitly)"
            echo "  --no-backup   Skip the pre-write snapshot of current prod content"
            echo "  --yes, -y     Skip the confirmation prompt (the dry-run still runs)"
            echo "  --dry-run     Show the prod diff and exit; never writes or snapshots"
            echo "  --help        Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 content/entry-40-reranking-summary.md"
            echo "  $0 --all"
            exit 0 ;;
        -*)
            echo -e "${RED}Error: Unknown option '$arg'${NC}"
            exit 1 ;;
        *)
            FILES+=("$arg") ;;
    esac
done

# Resolve the file list
if [ "$ALL" = true ]; then
    # shellcheck disable=SC2206
    FILES=(content/*.md)
    if [ ! -e "${FILES[0]}" ]; then
        echo -e "${RED}Error: no files in content/. Run dump_content first.${NC}"
        exit 1
    fi
elif [ "${#FILES[@]}" -eq 0 ]; then
    echo -e "${RED}Error: no files given. Pass content/*.md paths or --all.${NC}"
    echo "For help: $0 --help"
    exit 1
fi

# Pre-flight
if ! docker ps &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo -e "${RED}Error: container '${CONTAINER}' is not running${NC}"
    echo "Start it with: make dev   (or set CONTENT_CONTAINER=<name>)"
    exit 1
fi
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env not found (needed for production DATABASE_URL)${NC}"
    exit 1
fi

# Load production credentials from .env
DATABASE_URL="$(grep -E '^DATABASE_URL=' .env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
SECRET_KEY="$(grep -E '^SECRET_KEY=' .env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL missing from .env${NC}"
    exit 1
fi
# Azure Postgres requires SSL. Append sslmode=require if absent, respecting an
# existing query string.
if [[ "$DATABASE_URL" != *"sslmode="* ]]; then
    if [[ "$DATABASE_URL" == *"?"* ]]; then
        DATABASE_URL="${DATABASE_URL}&sslmode=require"
    else
        DATABASE_URL="${DATABASE_URL}?sslmode=require"
    fi
fi
export DATABASE_URL SECRET_KEY

# docker exec with production settings; secrets passed by NAME only (no values
# on the command line).
run_in_prod() {
    docker exec \
        -e DJANGO_SETTINGS_MODULE="$SETTINGS" \
        -e DATABASE_URL \
        -e SECRET_KEY \
        "$CONTAINER" python manage.py "$@"
}

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Promote content to PRODUCTION${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Files: ${#FILES[@]}"
echo ""

# Snapshot current prod content before overwriting (restore point).
# Skipped for a pure dry-run (nothing will be written).
if [ "$NO_BACKUP" = false ] && [ "$DRY_ONLY" = false ]; then
    TS="$(date +%Y%m%d-%H%M%S)"
    SNAP="$BACKUP_DIR/prod-content-$TS"
    echo -e "${BLUE}Snapshotting current prod content -> $SNAP/${NC}"
    mkdir -p "$SNAP"
    run_in_prod dump_content --all --output-dir "$SNAP" > /dev/null
    echo -e "${GREEN}✓ Prod snapshot saved (restore with: $0 $SNAP/<file>.md)${NC}"
    echo ""
elif [ "$DRY_ONLY" = false ]; then
    echo -e "${YELLOW}⚠️  Skipping prod snapshot (--no-backup)${NC}"
    echo ""
fi

# Mandatory dry-run
echo -e "${BLUE}Dry-run against production (no writes):${NC}"
echo ""
run_in_prod load_content "${FILES[@]}" --dry-run
echo ""

if [ "$DRY_ONLY" = true ]; then
    echo -e "${YELLOW}Dry-run only. No changes made to production.${NC}"
    exit 0
fi

# Confirmation gate
if [ "$ASSUME_YES" = false ]; then
    echo -e "${YELLOW}⚠️  This writes the changes above to the LIVE production database.${NC}"
    read -r -p "Type 'yes' to proceed: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Cancelled. No changes made to production."
        exit 0
    fi
    echo ""
fi

# Write
echo -e "${BLUE}Writing to production...${NC}"
run_in_prod load_content "${FILES[@]}"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Production content updated${NC}"
echo -e "${GREEN}================================${NC}"
if [ "$NO_BACKUP" = false ]; then
    echo ""
    echo -e "To roll back: ${YELLOW}$0 --all${NC} pointed at the snapshot, e.g."
    echo "  $0 $SNAP/<file>.md"
fi
echo ""
