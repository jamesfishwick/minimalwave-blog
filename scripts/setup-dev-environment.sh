#!/bin/bash
# Complete developer environment setup
# Consolidates: setup-dev-aliases.sh, enforce-dev-environment.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Development Environment Setup${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# 1. Set up shell aliases
setup_aliases() {
    echo -e "${BLUE}1. Setting up shell aliases...${NC}"

    ALIAS_CONTENT='
# Safe Django Migration Aliases - Auto-generated
alias django-makemigrations="echo \"⚠️  Use: make makemigrations\" && false"
alias django-migrate="echo \"⚠️  Use: make migrate-safe\" && false"
alias safe-migrate="make makemigrations && make migrate-safe"
alias safe-start="make dev-safe"
alias validate-mig="make validate-migrations"
alias test-mig="make test-migrations-clean"

echo "✅ Safe Django aliases loaded"
'

    if [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    else
        echo -e "${YELLOW}⚠️  Unknown shell. Skip alias setup.${NC}"
        return
    fi

    if grep -q "Safe Django Migration Aliases" "$SHELL_CONFIG" 2>/dev/null; then
        echo -e "${GREEN}✅ Aliases already configured${NC}"
    else
        echo "$ALIAS_CONTENT" >> "$SHELL_CONFIG"
        echo -e "${GREEN}✅ Aliases added to $SHELL_CONFIG${NC}"
        echo -e "${YELLOW}Run: source $SHELL_CONFIG${NC}"
    fi
}

# 2. Install pre-commit hooks
setup_precommit() {
    echo ""
    echo -e "${BLUE}2. Installing pre-commit hooks...${NC}"

    if ! command -v pre-commit &> /dev/null; then
        echo -e "${YELLOW}Installing pre-commit...${NC}"
        pip install pre-commit
    fi

    cd "$PROJECT_ROOT"
    pre-commit install
    pre-commit install --hook-type pre-push

    echo -e "${GREEN}✅ Pre-commit hooks installed${NC}"
}

# 3. Make scripts executable
setup_scripts() {
    echo ""
    echo -e "${BLUE}3. Making scripts executable...${NC}"

    chmod +x "$SCRIPT_DIR"/*.sh

    echo -e "${GREEN}✅ Scripts are executable${NC}"
}

# 4. Verify Docker setup
verify_docker() {
    echo ""
    echo -e "${BLUE}4. Verifying Docker setup...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not installed${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ docker-compose not installed${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Docker is installed${NC}"
}

# 5. Summary
print_summary() {
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✅ Setup Complete!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    if [ -n "$SHELL_CONFIG" ]; then
        echo "  1. source $SHELL_CONFIG        # Load aliases"
    fi
    echo "  2. make dev-safe               # Start development"
    echo "  3. make migrate-safe           # Apply migrations"
    echo ""
    echo -e "${BLUE}Available commands:${NC}"
    echo "  make dev-safe                  # Start with validation"
    echo "  make makemigrations            # Create migrations"
    echo "  make migrate-safe              # Apply migrations"
    echo "  make validate-migrations       # Validate migrations"
    echo "  safe-migrate                   # Complete migration workflow"
    echo ""
}

# Main
setup_aliases
setup_precommit
setup_scripts
verify_docker
print_summary
