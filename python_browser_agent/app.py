import os
import json
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
from dotenv import load_dotenv
# Use the direct browser instead for better JSON handling
from direct_browser import create_direct_browser 
import atexit
import signal
import argparse

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Global browser agent instance to prevent creating new browsers for each request
browser_agent = None

@app.route('/')
def index():
    """Serve the React app."""
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    """Handle all other routes to support React Router."""
    return send_from_directory(app.static_folder, 'index.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')

@socketio.on('chat message')
def handle_message(message):
    """Process chat messages from the client."""
    print(f"Received message: {message}")
    
    try:
        # Use the global browser agent
        global browser_agent
        if browser_agent is None:
            browser_agent = create_direct_browser(use_fake_llm=False)
        
        # Send initial thinking state
        socketio.emit('agent response', {
            'type': 'thinking',
            'message': 'Thinking...'
        })
        
        # Define progress callback
        def progress_callback(progress):
            socketio.emit('agent response', {
                'type': 'progress',
                'message': progress
            })
        
        # Define screenshot callback
        def screenshot_callback(screenshot_base64, description):
            socketio.emit('agent response', {
                'type': 'screenshot',
                'screenshot': screenshot_base64,
                'description': description
            })
        
        # Execute the instruction
        result = browser_agent.execute(
            instruction=message,
            callbacks={
                'on_progress': progress_callback,
                'on_screenshot': screenshot_callback
            }
        )
        
        # Send the final result
        socketio.emit('agent response', {
            'type': 'result',
            'message': result
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        socketio.emit('agent response', {
            'type': 'error',
            'message': f"An error occurred: {str(e)}"
        })

@socketio.on('model change')
def handle_model_change(model_name):
    """Handle model selection changes."""
    print(f"Model changed to: {model_name}")
    os.environ['OLLAMA_MODEL'] = model_name
    
    # Create a new browser agent with the new model
    global browser_agent
    if browser_agent is not None:
        # Release the old browser agent
        browser_agent = None
    
    socketio.emit('agent response', {
        'type': 'system',
        'message': f"Model changed to {model_name}"
    })

def cleanup_resources():
    """Clean up resources when the application exits."""
    global browser_agent
    if browser_agent is not None:
        print("Cleaning up browser resources...")
        try:
            browser_agent.close()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
        browser_agent = None

# Register cleanup function to be called when the app exits
atexit.register(cleanup_resources)

# Handle SIGTERM and SIGINT signals
def signal_handler(signum, frame):
    cleanup_resources()
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    try:
        # Parse command line arguments for port
        parser = argparse.ArgumentParser(description='Run the browser agent server')
        parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 3001)),
                           help='Port to run the server on')
        args = parser.parse_args()
        
        # Create initial browser agent
        browser_agent = create_direct_browser(use_fake_llm=False)
        # Get port from command line or environment variable
        port = args.port
        print(f"Starting server on port {port}")
        # Use the correct Flask-SocketIO configuration
        # Disable the reloader to prevent interference with the browser process
        socketio.run(app, port=port, host='0.0.0.0', debug=True, use_reloader=False)
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        cleanup_resources()
        exit(1) 
