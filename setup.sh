#!/bin/bash

# ============================================================================
# LexiVault AI - Initialization & Setup Script
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

log_info "Starting LexiVault AI setup..."

# Check for Docker
if ! check_command docker; then
    log_error "Docker is required but not installed. Please install Docker."
    exit 1
fi
log_success "Docker found"

# Check for Docker Compose
if ! check_command docker-compose; then
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is required but not installed"
        exit 1
    fi
fi
log_success "Docker Compose found"

# Check for aura-network
log_info "Checking for aura-network..."
if ! docker network ls | grep -q aura-network; then
    log_warning "aura-network not found, creating it..."
    docker network create aura-network
    log_success "aura-network created"
else
    log_success "aura-network found"
fi

# ============================================================================
# Environment Setup
# ============================================================================

if [ ! -f .env ]; then
    log_warning ".env file not found"
    if [ -f .env.example ]; then
        log_info "Creating .env from .env.example..."
        cp .env.example .env
        log_warning "Please edit .env with your actual values before proceeding!"
        log_warning "Critical variables that MUST be changed:"
        log_warning "  - SYSTEM_MASTER_KEY (generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
        log_warning "  - JWT_SECRET_KEY"
        log_warning "  - VAULT_DEV_ROOT_TOKEN_ID"
        exit 1
    fi
else
    log_success ".env file found"
fi

# ============================================================================
# Database Setup
# ============================================================================

log_info "Setting up database..."

# Get database credentials from .env
POSTGRES_HOST=$(grep '^POSTGRES_HOST=' .env | cut -d '=' -f2)
POSTGRES_PORT=$(grep '^POSTGRES_PORT=' .env | cut -d '=' -f2)
POSTGRES_USER=$(grep '^POSTGRES_USER=' .env | cut -d '=' -f2)
POSTGRES_PASSWORD=$(grep '^POSTGRES_PASSWORD=' .env | cut -d '=' -f2)
POSTGRES_DB=$(grep '^POSTGRES_DB=' .env | cut -d '=' -f2)

# Check if we can connect to Postgres
log_info "Testing database connection..."
if docker run --rm \
    --network aura-network \
    postgres:18-alpine \
    psql -h "$POSTGRES_HOST" \
         -U "$POSTGRES_USER" \
         -d postgres \
         -c "SELECT 1" \
    -w 2>/dev/null; then
    
    log_success "Database connection successful"
    
    # Create lexivault database if it doesn't exist
    log_info "Ensuring $POSTGRES_DB database exists..."
    docker run --rm \
        --network aura-network \
        -e PGPASSWORD="$POSTGRES_PASSWORD" \
        postgres:18-alpine \
        psql -h "$POSTGRES_HOST" \
             -U "$POSTGRES_USER" \
             -d postgres \
             -c "CREATE DATABASE $POSTGRES_DB;" \
        2>/dev/null || log_warning "Database may already exist (this is OK)"
    
    log_success "Database ready"
else
    log_error "Cannot connect to database at $POSTGRES_HOST:$POSTGRES_PORT"
    log_error "Make sure CASMARTS core-casmarts is running"
    exit 1
fi

# ============================================================================
# Docker Build & Launch
# ============================================================================

log_info "Building Docker images..."
if docker compose build; then
    log_success "Docker images built successfully"
else
    log_error "Failed to build Docker images"
    exit 1
fi

log_info "Starting LexiVault services..."
if docker compose up -d; then
    log_success "LexiVault services started"
else
    log_error "Failed to start LexiVault services"
    exit 1
fi

# ============================================================================
# Health Checks
# ============================================================================

log_info "Waiting for services to be ready..."
sleep 5

# Backend health check
log_info "Checking backend health..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        log_success "Backend is healthy"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_warning "Backend took longer to start than expected"
        log_info "Check logs with: docker compose logs flask_backend"
    fi
    sleep 1
done

# Frontend check
log_info "Checking frontend..."
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    log_success "Frontend is healthy"
else
    log_warning "Frontend may still be starting"
    log_info "Check logs with: docker compose logs frontend"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
log_success "LexiVault AI is ready!"
echo ""
echo -e "${BLUE}📍 Access Points:${NC}"
echo "  Frontend:  ${GREEN}http://localhost:8501${NC}"
echo "  Backend:   ${GREEN}http://localhost:5000${NC}"
echo "  API Docs:  ${GREEN}http://localhost:5000/docs${NC} (when implemented)"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  View logs:       ${YELLOW}docker compose logs -f${NC}"
echo "  Stop services:   ${YELLOW}docker compose down${NC}"
echo "  Restart backend: ${YELLOW}docker compose restart flask_backend${NC}"
echo "  Restart worker:  ${YELLOW}docker compose restart celery_worker${NC}"
echo ""
echo -e "${BLUE}🔗 Next Steps:${NC}"
echo "  1. Open ${GREEN}http://localhost:8501${NC} in your browser"
echo "  2. Test API: ${YELLOW}curl http://localhost:5000/health${NC}"
echo "  3. Check backend logs: ${YELLOW}docker compose logs -f flask_backend${NC}"
echo ""
