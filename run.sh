#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║         ARIA — Voice AI Agent Setup              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check for API key
if [ -z "$GEMINI_API_KEY" ]; then
  if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
  fi
fi

if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
  echo "⚠  GEMINI_API_KEY not set!"
  echo "   Edit the .env file and add your key:"
  echo "   GEMINI_API_KEY=AIza..."
  echo ""
  exit 1
fi

echo "✓ Gemini API key found"
echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
# Create venv if needed
if [ ! -f .venv/bin/activate ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Start server
echo "🚀 Starting ARIA server on http://localhost:8000"
echo "   Open Chrome and go to: http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
