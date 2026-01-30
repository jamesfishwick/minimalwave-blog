#!/bin/bash
# Unified Azure operations
# Consolidates: fix-azure-storage.sh, diagnose_production.sh, fix-site-domain-remote.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="minimalwave-blog"
RESOURCE_GROUP="minimalwave-blog-rg"

usage() {
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  --fix-storage    Fix Azure Blob Storage configuration"
    echo "  --diagnose       Download and analyze production logs"
    echo "  --fix-domain     Fix Site domain configuration"
    echo "  --health-check   Run comprehensive health check"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --fix-storage        # Fix storage configuration"
    echo "  $0 --diagnose           # Diagnose production issues"
    echo "  $0 --health-check       # Check all Azure resources"
}

load_azure_resources() {
    if [ -f "$PROJECT_ROOT/.azure-resources" ]; then
        source "$PROJECT_ROOT/.azure-resources"
    else
        echo -e "${RED}Error: .azure-resources file not found${NC}"
        exit 1
    fi
}

fix_storage() {
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}Azure Storage Configuration Fixer${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""

    load_azure_resources

    echo -e "${BLUE}1. Checking current App Service environment variables...${NC}"
    az webapp config appsettings list \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "[?name=='AZURE_STORAGE_ACCOUNT_NAME' || name=='AZURE_STORAGE_ACCOUNT_KEY'].{name:name, value:value}" \
        -o table

    echo ""
    echo -e "${BLUE}2. Setting Azure Storage environment variables...${NC}"
    az webapp config appsettings set \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --settings \
            AZURE_STORAGE_ACCOUNT_NAME="$AZURE_STORAGE_ACCOUNT_NAME" \
            AZURE_STORAGE_ACCOUNT_KEY="$AZURE_STORAGE_KEY" \
        --output table

    echo ""
    echo -e "${GREEN}✅ Configuration Updated!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Restart your App Service:"
    echo "   az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "2. Re-upload images through Django admin"
    echo "3. Verify blobs: az storage blob list --account-name $AZURE_STORAGE_ACCOUNT_NAME --container-name media"
}

diagnose_production() {
    echo -e "${BLUE}==== Diagnosing Production ====${NC}"

    SANDBOX_DIR="$PROJECT_ROOT/.claude-sandbox"
    mkdir -p "$SANDBOX_DIR"

    echo -e "${BLUE}1. Waiting for deployment to complete...${NC}"
    sleep 30

    echo -e "${BLUE}2. Downloading latest logs...${NC}"
    az webapp log download \
        --resource-group $RESOURCE_GROUP \
        --name $APP_NAME \
        --log-file "$SANDBOX_DIR/prod_diagnosis.zip"

    echo -e "${BLUE}3. Extracting logs...${NC}"
    unzip -q "$SANDBOX_DIR/prod_diagnosis.zip" -d "$SANDBOX_DIR/prod_diagnosis/"

    echo -e "${BLUE}4. Checking for migration errors...${NC}"
    grep -A20 -B5 "migrations\|migrate" "$SANDBOX_DIR/prod_diagnosis/LogFiles/"*docker.log 2>/dev/null | tail -50 || echo "No migration errors found"

    echo -e "${BLUE}5. Checking for model mismatch errors...${NC}"
    grep -A5 "Your models in app" "$SANDBOX_DIR/prod_diagnosis/LogFiles/"*docker.log 2>/dev/null | tail -20 || echo "No model mismatch errors found"

    echo -e "${BLUE}6. Testing admin access...${NC}"
    curl -I https://jamesfishwick.com/admin/ 2>/dev/null | grep -E "HTTP|500" || echo "Admin check failed"

    echo ""
    echo -e "${GREEN}✅ Diagnosis complete! Check $SANDBOX_DIR/prod_diagnosis/ for full logs${NC}"
}

fix_domain() {
    echo -e "${BLUE}Fixing Site domain configuration...${NC}"

    echo -e "${YELLOW}This requires Django shell access on Azure${NC}"
    echo "Run this command on Azure:"
    echo ""
    echo "  az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo ""
    echo "Then in the shell:"
    echo "  python manage.py shell"
    echo "  from django.contrib.sites.models import Site"
    echo "  site = Site.objects.get(id=1)"
    echo "  site.domain = 'jamesfishwick.com'"
    echo "  site.name = 'Minimal Wave'"
    echo "  site.save()"
    echo "  exit()"
}

health_check() {
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}Azure Health Check${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""

    echo -e "${BLUE}1. Checking App Service status...${NC}"
    az webapp show \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "{name:name, state:state, hostNames:hostNames}" \
        -o table

    echo ""
    echo -e "${BLUE}2. Checking recent deployments...${NC}"
    az webapp deployment list \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "[0:3].{id:id, status:status, author:author, message:message}" \
        -o table

    echo ""
    echo -e "${BLUE}3. Testing site availability...${NC}"
    if curl -f -s -o /dev/null --max-time 10 https://jamesfishwick.com/; then
        echo -e "${GREEN}✓ Homepage OK${NC}"
    else
        echo -e "${RED}✗ Homepage FAILED${NC}"
    fi

    if curl -f -s -o /dev/null --max-time 10 https://jamesfishwick.com/admin/; then
        echo -e "${GREEN}✓ Admin OK${NC}"
    else
        echo -e "${RED}✗ Admin FAILED${NC}"
    fi

    echo ""
    echo -e "${BLUE}4. Checking environment variables...${NC}"
    az webapp config appsettings list \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "[?contains(name, 'DJANGO') || contains(name, 'AZURE')].{name:name, slotSetting:slotSetting}" \
        -o table

    echo ""
    echo -e "${GREEN}✅ Health check complete${NC}"
}

# Main
MODE="${1:---help}"

case "$MODE" in
    --fix-storage)
        fix_storage
        ;;
    --diagnose)
        diagnose_production
        ;;
    --fix-domain)
        fix_domain
        ;;
    --health-check)
        health_check
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
