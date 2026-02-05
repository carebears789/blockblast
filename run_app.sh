#!/bin/bash
# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Flask app
echo "Starting Block Blast Assistant..."
echo "Open your browser to: http://localhost:5000"
python3 app.py
