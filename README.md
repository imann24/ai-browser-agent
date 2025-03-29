# Browser Agent

A chat interface for browser automation using Python, browser-use, and Ollama.

This project allows you to chat with an AI agent that can control a web browser to perform tasks on your behalf. The agent uses local LLMs through Ollama.

## Project Structure

- `python_browser_agent/` - Python backend for browser automation
- `frontend/` - React TypeScript frontend with Tailwind CSS

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/browser-agent.git
cd browser-agent
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install browser-use langchain-community langchain-core
```

4. Ensure Ollama is installed and running:
```bash
# Install from https://ollama.ai first, then:
ollama serve
```

5. Pull a compatible LLM model:
```bash
ollama pull llama3
```

6. Set up the frontend (one-time setup):
```bash
# Build the React frontend
./build.sh
```

## Usage

### Quick Start

The recommended way to use Browser Agent is with the Direct Browser implementation:

```bash
# Run with default Ollama LLM
python -m python_browser_agent.run_direct_browser

# Run with a specific instruction
python -m python_browser_agent.run_direct_browser --instruction "Go to weather.com and tell me the forecast"

# Run with fake LLM (for testing)
python -m python_browser_agent.run_direct_browser --fake-llm
```

### Web Interface

You can also use the web-based chat interface with the React frontend:

1. Start the server:
```bash
python -m python_browser_agent.app
```

2. Open your browser and navigate to:
```
http://localhost:3001
```

3. Enter your instructions in the chat interface and watch the agent perform the requested tasks.

### Frontend Development

If you want to work on the frontend:

1. Option 1: Run both servers separately (recommended for more reliable Python imports):
```bash
# In terminal 1
cd frontend
npm install
npm start

# In terminal 2
# Make sure you're in the root directory
python -m python_browser_agent.app
```

2. Option 2: Run everything in a single terminal:
```bash
# First time setup
cd frontend && npm install && npm run start:all

# Subsequent runs
cd frontend && npm run start:all
```

**Note**: If you encounter Python import issues with the single-terminal approach, use Option 1 instead, or modify your PYTHONPATH environment variable manually:

```bash
# On macOS/Linux
PYTHONPATH=$PYTHONPATH:. python -m python_browser_agent.app

# On Windows PowerShell
$env:PYTHONPATH="$env:PYTHONPATH;." ; python -m python_browser_agent.app
```

### Example Commands

Here are some examples of what you can ask the browser agent to do:

- "Search for the latest news about artificial intelligence"
- "Find recipes for vegetarian pasta dishes"
- "Look up the weather forecast for New York City"
- "Go to GitHub and show me trending Python repositories"
- "Visit Wikipedia and find information about quantum computing"

### Advanced Configuration

You can configure the application by setting environment variables or editing the `.env` file:

```
# Server settings
PORT=3001
SECRET_KEY=your_secret_key_here

# Ollama settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Recent Changes

The project has been updated with:

- React TypeScript frontend replacing the original HTML/JS implementation
- Tailwind CSS for modern styling and responsive design
- Full dark/light mode implementation with persistent theme preferences
- Improved screenshot gallery with navigation controls
- Command history with arrow key navigation
- Backend modifications to serve the React app
- Fixed Python import issues in development scripts

## Troubleshooting

If you encounter issues:

1. Ensure Ollama is running (`ollama serve`)
2. Check that you've pulled the required model (`ollama pull llama3`)
3. Try using the `--fake-llm` flag to test without LLM dependencies
4. Look for error messages in the console output
5. Verify your browser can be automated (Chrome/Firefox recommended)
6. For frontend issues, check the browser console for errors
7. If you see Python import errors, make sure you're running the app from the project root directory

## Setup and Usage

Please see the [README in the python_browser_agent directory](./python_browser_agent/README.md) for additional setup instructions and usage details.

## Key Features

- Chat with an AI agent that can browse the web
- Real-time feedback on agent actions
- Support for different local Ollama models
- Modern React TypeScript frontend with Tailwind CSS
- Dark/light mode support
- Screenshot gallery with navigation
- Command history
- Socket.IO real-time communication
- Responsive design for various screen sizes

## License

MIT 
