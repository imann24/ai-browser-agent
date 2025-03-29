# Browser Agent Frontend

This is a React TypeScript frontend for the Browser Agent application, using Tailwind CSS for styling.

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

## Features

- Real-time chat interface with the browser agent
- Dark/light mode toggle
- Command history navigation (using up/down arrows)
- Screenshot gallery with navigation
- Responsive design using Tailwind CSS

## Project Structure

- `src/components/` - React components
  - `Navbar.tsx` - Top navigation bar with theme toggle
  - `ChatContainer.tsx` - Main chat container
  - `ChatMessages.tsx` - Messages display
  - `ChatInput.tsx` - Input field with history
  - `ScreenshotGallery.tsx` - Gallery for screenshots

## Backend Connection

The frontend connects to the Flask backend running on port 3001 using Socket.IO. 
