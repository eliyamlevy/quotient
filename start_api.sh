#!/bin/bash

# Quotient API Startup Script
# This script starts the FastAPI server for the Quotient inventory management system

echo "🚀 Starting Quotient API Server..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "api.py" ]; then
    echo "❌ Error: api.py not found. Please run this script from the project root."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Some features may not work."
    echo "   Create .env file with your Hugging Face token:"
    echo "   HUGGINGFACE_TOKEN=your_token_here"
fi

# Check if conda environment is activated
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "⚠️  Warning: No conda environment detected."
    echo "   Make sure you're in the quotient conda environment."
fi

# Install FastAPI dependencies if needed
echo "📦 Checking FastAPI dependencies..."
python -c "import fastapi" 2>/dev/null || {
    echo "Installing FastAPI dependencies..."
    pip install fastapi uvicorn[standard] python-multipart requests
}

# Start the API server
echo "🌐 Starting API server on http://localhost:8000"
echo "📚 API documentation will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the API server
python api.py 