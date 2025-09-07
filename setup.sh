#!/bin/bash

# Auralis Project Setup Script
# This script automatically sets up the virtual environment and installs dependencies

set -e  # Exit on any error

echo "🎵 Setting up Auralis project..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.11+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
if [ -f "backend/requirements.txt" ]; then
    echo "📚 Installing backend dependencies..."
    pip install -r backend/requirements.txt
else
    echo "⚠️  backend/requirements.txt not found"
fi

# Create .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend/.env file..."
    cat > backend/.env << EOF
# Auralis Backend Environment Variables
DEBUG=true
LOG_LEVEL=info
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
    echo "✅ Created backend/.env with default values"
else
    echo "✅ backend/.env already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To activate the virtual environment manually:"
echo "  source venv/bin/activate"
echo ""
echo "To start the backend:"
echo "  cd backend && python -m uvicorn app.main:app --reload"
echo ""
echo "To start all services with Docker:"
echo "  make up"
echo ""
echo "Virtual environment is now active in this shell session."
