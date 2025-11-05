#!/bin/bash

# ============================================================================
# GETLOOD Platform - Quick Start Script
# ============================================================================
# This script automates the deployment of the GETLOOD platform
# Usage: ./quickstart.sh [command]
# Commands: start, stop, restart, logs, clean, setup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    GETLOOD PLATFORM                            ║"
    echo "║              Multi-Tenant AI Orchestration Platform            ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_dependencies() {
    print_info "Checking dependencies..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker found: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose found: $(docker compose version)"

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    print_success "Docker daemon is running"
}

setup_env() {
    print_info "Setting up environment..."

    # Check if .env exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env

        # Generate JWT secret
        if command -v openssl &> /dev/null; then
            JWT_SECRET=$(openssl rand -hex 32)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
            else
                # Linux
                sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
            fi
            print_success "Generated secure JWT secret"
        else
            print_warning "OpenSSL not found. Please update JWT_SECRET in .env manually."
        fi

        print_warning "Please update .env with your API keys and configuration"
        print_info "Opening .env file for editing..."
        sleep 2
        ${EDITOR:-nano} .env
    else
        print_success ".env file already exists"
    fi
}

create_directories() {
    print_info "Creating required directories..."

    # Create directories if they don't exist
    mkdir -p logs
    mkdir -p database/init
    mkdir -p nginx/ssl
    mkdir -p monitoring/grafana/{dashboards,datasources}
    mkdir -p monitoring

    print_success "Directories created"
}

create_configs() {
    print_info "Creating configuration files..."

    # Create prometheus.yml if it doesn't exist
    if [ ! -f "monitoring/prometheus.yml" ]; then
        cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'getlood-api'
    static_configs:
      - targets: ['getlood-api:8000']
    metrics_path: '/metrics'
EOF
        print_success "Created prometheus.yml"
    fi

    # Create nginx.conf if it doesn't exist
    if [ ! -f "nginx/nginx.conf" ]; then
        cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api {
        server getlood-api:8000;
    }

    upstream frontend {
        server getlood-frontend:5173;
    }

    server {
        listen 80;
        server_name localhost;

        # API
        location /api {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket
        location /ws {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 86400;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
EOF
        print_success "Created nginx.conf"
    fi

    # Create database init script if it doesn't exist
    if [ ! -f "database/init/01-init.sql" ]; then
        cat > database/init/01-init.sql << 'EOF'
-- GETLOOD Platform Database Initialization

-- Create GETLOOD database
CREATE DATABASE IF NOT EXISTS getlood;

-- Connect to GETLOOD database
\c getlood;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Desktops table
CREATE TABLE IF NOT EXISTS desktops (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_desktops_user_id ON desktops(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_desktops_updated_at BEFORE UPDATE ON desktops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EOF
        print_success "Created database init script"
    fi
}

pull_images() {
    print_info "Pulling Docker images..."
    docker compose pull
    print_success "Images pulled successfully"
}

build_images() {
    print_info "Building custom Docker images..."
    docker compose build --no-cache
    print_success "Images built successfully"
}

start_services() {
    print_info "Starting services..."
    docker compose up -d
    print_success "Services started successfully"
}

wait_for_services() {
    print_info "Waiting for services to be healthy..."

    max_attempts=60
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker compose ps | grep -q "unhealthy"; then
            print_warning "Some services are unhealthy, waiting... ($((attempt+1))/$max_attempts)"
            sleep 5
            ((attempt++))
        else
            print_success "All services are healthy!"
            return 0
        fi
    done

    print_error "Services failed to become healthy within timeout"
    docker compose ps
    return 1
}

show_status() {
    print_info "Service Status:"
    docker compose ps
    echo ""

    print_info "Access URLs:"
    echo -e "${GREEN}Frontend:${NC}    http://localhost:80"
    echo -e "${GREEN}API Docs:${NC}    http://localhost:8000/docs"
    echo -e "${GREEN}MindsDB:${NC}     http://localhost:47334"
    echo -e "${GREEN}Grafana:${NC}     http://localhost:3000 (admin/admin)"
    echo -e "${GREEN}Prometheus:${NC}  http://localhost:9090"
    echo ""
}

stop_services() {
    print_info "Stopping services..."
    docker compose down
    print_success "Services stopped"
}

clean_all() {
    print_warning "This will remove all containers, volumes, and data. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Cleaning up..."
        docker compose down -v --remove-orphans
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

show_logs() {
    service=${1:-}
    if [ -z "$service" ]; then
        docker compose logs -f
    else
        docker compose logs -f "$service"
    fi
}

# ============================================================================
# Main Script
# ============================================================================

print_header

command=${1:-start}

case "$command" in
    setup)
        print_info "Setting up GETLOOD Platform..."
        check_dependencies
        setup_env
        create_directories
        create_configs
        pull_images
        build_images
        start_services
        wait_for_services
        show_status
        print_success "Setup complete! 🚀"
        ;;

    start)
        print_info "Starting GETLOOD Platform..."
        check_dependencies
        if [ ! -f ".env" ]; then
            setup_env
        fi
        create_directories
        create_configs
        start_services
        wait_for_services
        show_status
        ;;

    stop)
        stop_services
        ;;

    restart)
        stop_services
        start_services
        wait_for_services
        show_status
        ;;

    logs)
        show_logs "${2:-}"
        ;;

    status)
        show_status
        ;;

    build)
        check_dependencies
        build_images
        ;;

    clean)
        clean_all
        ;;

    *)
        echo "Usage: $0 {setup|start|stop|restart|logs|status|build|clean}"
        echo ""
        echo "Commands:"
        echo "  setup    - Initial setup (first time only)"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show logs (optionally specify service)"
        echo "  status   - Show service status and URLs"
        echo "  build    - Rebuild Docker images"
        echo "  clean    - Remove all containers and volumes"
        exit 1
        ;;
esac
