#!/bin/bash

# Labor Market RAG - Quick Start Script

echo "🚀 Labor Market RAG - Quick Start"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OpenAI API key not found in environment"
    echo ""
    echo "Please set your API key:"
    echo "  export OPENAI_API_KEY='your-key-here'"
    echo ""
    echo "Or create .streamlit/secrets.toml with:"
    echo "  OPENAI_API_KEY = 'your-key-here'"
    echo ""
else
    echo "✅ OpenAI API key found"
fi

echo ""
echo "🎯 Starting application..."
echo ""
echo "Access the application at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Run Streamlit app
streamlit run app/main.py
