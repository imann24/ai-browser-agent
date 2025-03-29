# Browser Agent

This package provides tools for automating browser tasks using LLMs.

## Overview

There are two implementations available:

1. **Original Browser Agent** (browser_agent.py): Uses the `browser-use` library's `Agent` class, which has compatibility issues with version 0.1.40.

2. **Direct Browser** (direct_browser.py): A direct implementation that doesn't rely on the `Agent.run()` method, providing more reliable execution.

## Installation

```bash
pip install browser-use langchain-community langchain-core
```

## Usage

### Direct Browser (Recommended)

You can run the Direct Browser with either a fake LLM (for testing) or the Ollama LLM:

```bash
# Run with fake LLM (for testing)
python -m python_browser_agent.run_direct_browser --fake-llm

# Run with Ollama LLM (default)
python -m python_browser_agent.run_direct_browser

# Run with custom instruction
python -m python_browser_agent.run_direct_browser --instruction "Go to weather.com and tell me the forecast"
```

### Original Browser Agent (Not recommended with browser-use 0.1.40)

If you want to try the original implementation:

```python
from python_browser_agent import create_browser_agent

agent = create_browser_agent()
result = agent.execute("Go to example.com and tell me what's on the page")
print(result)
```

## Features

- Robust error handling with SafeJsonChatOllamaWrapper to handle invalid JSON responses
- Detailed logging for debugging
- Screenshot capture during navigation
- Support for using either fake LLM responses or Ollama models

## Troubleshooting

If you encounter issues with the original browser agent, try:

1. Using the Direct Browser implementation
2. Setting `use_fake_llm=True` to isolate LLM-related issues
3. Checking the logs for detailed error information 

## Implementation Details

The Direct Browser implementation bypasses the compatibility issues with `browser-use` by directly:

1. Creating and managing browser instances
2. Processing LLM responses and handling JSON validation
3. Executing browser actions based on parsed responses
4. Capturing page content and sending it back to the LLM

This approach gives you more control over the execution flow and error handling.

## Prerequisites

- Python 3.8+
- Ollama installed locally (https://ollama.ai) with models like llama3, mistral, etc.
- A modern web browser

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/browser-agent.git
cd browser-agent/python_browser_agent
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Make sure Ollama is running:
```bash
ollama serve
```

5. Ensure you have at least one model pulled:
```bash
ollama pull llama3
```

6. Set up environment variables (or edit the .env file):
```
# Server settings
PORT=3000
SECRET_KEY=your_secret_key_here

# Ollama settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Running the Application

1. Start the server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:3000
```

## How It Works

This project integrates:

- **browser-use**: A Python framework for LLMs to control a web browser
- **Ollama**: A local LLM runner that supports various models
- **Flask/Socket.IO**: For the web server and real-time communication

The agent receives instructions from the user, processes them using the local LLM through Ollama, and then executes actions using browser-use.

## Example Commands

Here are some examples of what you can ask the browser agent to do:

- "Search for the latest news about artificial intelligence"
- "Find recipes for vegetarian pasta dishes"
- "Look up the weather forecast for New York City"
- "Find information about the population of Tokyo"
- "Search for tutorials on Python web scraping"

## License

MIT 
