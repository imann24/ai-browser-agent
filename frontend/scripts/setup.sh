#!/bin/bash
# Setup script for the browser agent frontend

# Navigate to frontend directory
cd "$(dirname "$0")/.."

# Install dependencies
echo "Installing frontend dependencies..."
npm install

echo "Setup complete! You can now run 'npm start' to start the development server." 
