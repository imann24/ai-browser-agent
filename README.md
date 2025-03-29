# Browser Agent

A chat interface for browser automation using Python, browser-use, and Ollama.

This project allows you to chat with an AI agent that can control a web browser to perform tasks on your behalf. The agent uses local LLMs through Ollama.

## Project Structure

All project files are contained in the `python_browser_agent` directory.

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

You can also use the web-based chat interface:

1. Start the server:
```bash
python python_browser_agent/app.py
```

2. Open your browser and navigate to:
```
http://localhost:3000
```

3. Enter your instructions in the chat interface and watch the agent perform the requested tasks.

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
PORT=3000
SECRET_KEY=your_secret_key_here

# Ollama settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Troubleshooting

If you encounter issues:

1. Ensure Ollama is running (`ollama serve`)
2. Check that you've pulled the required model (`ollama pull llama3`)
3. Try using the `--fake-llm` flag to test without LLM dependencies
4. Look for error messages in the console output
5. Verify your browser can be automated (Chrome/Firefox recommended)

## Setup and Usage

Please see the [README in the python_browser_agent directory](./python_browser_agent/README.md) for additional setup instructions and usage details.

## Key Features

- Chat with an AI agent that can browse the web
- Real-time feedback on agent actions
- Support for different local Ollama models
- Web-based UI with real-time updates
- Screenshot capture during navigation
- Robust error handling

## License

MIT 
