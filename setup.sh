#!/bin/bash

# West Bengal Electoral Data - Quick Setup Script

set -e  # Exit on error

echo "======================================"
echo "West Bengal Electoral Data Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3 not found"; exit 1; }
echo "✓ Python 3 found"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create configuration
echo "Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    cp config/config.example.yaml config/config.yaml
    echo "✓ Configuration file created: config/config.yaml"
    echo "  (Edit this file to customize settings)"
else
    echo "✓ Configuration file already exists"
fi
echo ""

# Create data directories
echo "Creating data directories..."
mkdir -p data/pdfs data/output data/cache logs
echo "✓ Data directories created"
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x scripts/*.py web/app.py
echo "✓ Scripts are now executable"
echo ""

echo "======================================"
echo "Setup Complete! 🎉"
echo "======================================"
echo ""
echo "Quick Start:"
echo ""
echo "1. Fetch metadata:"
echo "   python scripts/fetch_metadata.py --all"
echo ""
echo "2. Download PDFs (example for AC 139):"
echo "   python scripts/download_pdfs.py --ac 139"
echo ""
echo "3. Extract voter data:"
echo "   python scripts/extract_voters.py --ac 139"
echo ""
echo "4. Validate data:"
echo "   python scripts/validate_data.py --ac 139"
echo ""
echo "5. Start web interface:"
echo "   python web/app.py"
echo ""
echo "For more information, see README.md"
echo ""
