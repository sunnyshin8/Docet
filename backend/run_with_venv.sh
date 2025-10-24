#!/bin/bash
# Script to ensure virtual environment is active before running commands

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Virtual environment not active!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

# Check if we're in the backend directory
if [[ ! -f "requirements.txt" ]] || [[ ! -d "app" ]]; then
    echo "❌ Not in backend directory!"
    echo "Please run: cd /home/cipher/Documents/Docet/backend"
    exit 1
fi

# Run the command passed as argument
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <command>"
    exit 1
fi

echo "🚀 Running: $@"
exec "$@"