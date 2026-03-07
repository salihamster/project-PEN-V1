#!/bin/bash
# Move to the script's directory for portability
cd "$(dirname "$0")"
echo "Starting PEN Web Server..."
python3 web_server.py
