#!/bin/bash
# Quick Docker test script for OpenAI Whisper Web Interface
# Tests both production and development containers

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install docker-compose."
    exit 1
fi

echo "🐳 Docker Test for OpenAI Whisper Web Interface"
echo "=============================================="

case "${1:-test}" in
    "build")
        print_info "Building Docker image..."
        docker build -t whisper-web-interface:latest .
        print_success "Docker image built successfully"
        ;;
    
    "test")
        print_info "Starting quick test (production mode)..."
        
        # Build if image doesn't exist
        if ! docker images | grep -q whisper-web-interface; then
            print_info "Image not found, building..."
            docker build -t whisper-web-interface:latest .
        fi
        
        # Start container
        print_info "Starting container..."
        docker-compose up -d
        
        # Wait for container to be ready
        print_info "Waiting for application to start..."
        sleep 30
        
        # Test health endpoint
        print_info "Testing health endpoint..."
        if curl -k -f https://localhost:5001/health >/dev/null 2>&1; then
            print_success "✅ Health check passed"
        else
            print_error "❌ Health check failed"
            print_info "Container logs:"
            docker-compose logs whisper-app
            exit 1
        fi
        
        # Test main interface
        print_info "Testing main interface..."
        if curl -k -f https://localhost:5001/ >/dev/null 2>&1; then
            print_success "✅ Main interface accessible"
        else
            print_warning "⚠️  Main interface test failed"
        fi
        
        print_success "🎉 Docker test completed successfully!"
        print_info ""
        print_info "🌐 Access URLs:"
        print_info "  - Main Interface: https://localhost:5001"
        print_info "  - Admin Panel: https://localhost:5001/admin"
        print_info "  - API Docs: https://localhost:5001/docs"
        print_info "  - Health Check: https://localhost:5001/health"
        print_info ""
        print_warning "🔒 Note: Browser will show SSL warnings (self-signed certificate)"
        print_info ""
        print_info "To stop: docker-compose down"
        ;;
        
    "dev")
        print_info "Starting development test..."
        docker-compose -f docker-compose.dev.yml up -d
        
        sleep 30
        
        if curl -k -f https://localhost:5001/health >/dev/null 2>&1; then
            print_success "✅ Development container running"
            print_info "Development mode: https://localhost:5001"
        else
            print_error "❌ Development container failed"
            docker-compose -f docker-compose.dev.yml logs
            exit 1
        fi
        ;;
        
    "fallback")
        print_info "Testing fallback mode..."
        docker-compose -f docker-compose.dev.yml --profile fallback up -d
        
        sleep 20
        
        if curl -k -f https://localhost:5003/health >/dev/null 2>&1; then
            print_success "✅ Fallback container running"
            print_info "Fallback mode: https://localhost:5003"
        else
            print_error "❌ Fallback container failed"
            docker-compose -f docker-compose.dev.yml logs whisper-fallback-dev
            exit 1
        fi
        ;;
        
    "stop")
        print_info "Stopping all containers..."
        docker-compose down
        docker-compose -f docker-compose.dev.yml down
        docker-compose -f docker-compose.dev.yml --profile fallback down
        print_success "All containers stopped"
        ;;
        
    "clean")
        print_info "Cleaning up Docker resources..."
        docker-compose down -v
        docker-compose -f docker-compose.dev.yml down -v
        docker system prune -f
        print_success "Docker cleanup completed"
        ;;
        
    "logs")
        print_info "Showing container logs..."
        docker-compose logs -f
        ;;
        
    *)
        echo "Usage: $0 {build|test|dev|fallback|stop|clean|logs}"
        echo ""
        echo "Commands:"
        echo "  build     - Build Docker image"
        echo "  test      - Run production container test"
        echo "  dev       - Run development container"
        echo "  fallback  - Test fallback mode"
        echo "  stop      - Stop all containers"
        echo "  clean     - Clean up all Docker resources"
        echo "  logs      - Show container logs"
        exit 1
        ;;
esac
