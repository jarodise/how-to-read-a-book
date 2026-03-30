#!/bin/bash
set -e

echo "📦 Installing How To Read a Book skill dependencies..."

# Check Python 3
echo "🔍 Checking Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "📥 Installing Python packages..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Install playwright browser
echo "🎭 Installing Playwright browser..."
playwright install chromium 2>/dev/null || echo "⚠️  Playwright browser install may require manual intervention"

# Verify notebooklm CLI
echo "✅ Verifying NotebookLM CLI..."
if ! command -v notebooklm &> /dev/null; then
    echo "⚠️  notebooklm command not found in PATH"
    echo "   Try: source .venv/bin/activate && notebooklm --version"
    exit 1
fi

# Check authentication
echo "🔐 Checking NotebookLM authentication..."
if notebooklm list &> /dev/null; then
    echo "✅ NotebookLM authenticated"
else
    echo "⚠️  NotebookLM not authenticated"
    echo "   Run: notebooklm login"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "  1. If not authenticated: notebooklm login"
echo "  2. Run: python3 scripts/run.py /path/to/your/book.epub"
echo ""
