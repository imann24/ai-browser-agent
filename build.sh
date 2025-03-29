#!/bin/bash
# Build script for browser agent with React frontend

# Make sure we're in the right directory
cd "$(dirname "$0")"

echo "===== Building Browser Agent ====="

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "frontend/node_modules" ]; then
  echo "Installing frontend dependencies..."
  cd frontend
  npm install
  cd ..
fi

# Build the frontend
echo "Building React frontend..."
cd frontend
npm run build
cd ..

# Check if build was successful
if [ ! -d "frontend/build" ]; then
  echo "Frontend build failed. Exiting."
  exit 1
fi

echo "Frontend build successful. Built files are in frontend/build/"
echo "To run the application, use: python -m python_browser_agent.app"
echo "===== Build Complete =====" 
