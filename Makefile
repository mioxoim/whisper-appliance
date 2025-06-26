.PHONY: install test run clean quick-test

# Variables
PYTHON = ./venv/bin/python
PIP = ./venv/bin/pip
PROJECT_DIR = /home/commander/Code/whisper-appliance

install:
	@echo "🔧 Setting up development environment..."
	cd $(PROJECT_DIR) && python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "📦 Installing WhisperS2T from GitHub..."
	$(PIP) install git+https://github.com/shashikg/WhisperS2T.git
	@echo "✅ Development environment ready!"

test:
	@echo "🧪 Running WhisperS2T integration tests..."
	$(PYTHON) src/whisper-service/test_whisper.py

run:
	@echo "🚀 Starting development server..."
	cd $(PROJECT_DIR) && $(PYTHON) src/webgui/backend/main.py

clean:
	@echo "🧹 Cleaning up..."
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

quick-test:
	@echo "⚡ Quick system test..."
	curl -s http://localhost:5000/api/status | python3 -m json.tool || echo "Server not running"

structure:
	@echo "📁 Project structure:"
	tree -I 'venv|__pycache__|*.pyc'
