import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Callable, Optional, List, Any, Union

# Import browser functionality directly
from browser_use import Browser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_community.chat_models.fake import FakeListChatModel

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("direct_browser")
logger.setLevel(logging.DEBUG)

# Add file handler
file_handler = logging.FileHandler("direct_browser.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Enable Playwright debug logging
# os.environ["DEBUG"] = "pw:api,pw:browser"
# os.environ["PLAYWRIGHT_DRIVER_VERBOSE"] = "1"

# Check if playwright is installed and install if needed
try:
    import playwright
except ImportError:
    import subprocess
    import sys
    logger.warning("Playwright not found, installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install"])
    logger.info("Playwright installed successfully")

from playwright.async_api import async_playwright

# Create screenshots directory if it doesn't exist
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
logger.info(f"Screenshots will be saved in: {SCREENSHOTS_DIR}")

class SafeJsonChatOllamaWrapper:
    """A wrapper around ChatOllama that ensures valid JSON output."""
    
    def __init__(self, chat_model, default_fallback_msg=None):
        """Initialize the wrapper with a ChatOllama model."""
        self.chat_model = chat_model
        self.default_fallback_msg = default_fallback_msg or {
            "action": "finish", 
            "result": "I encountered an issue and couldn't complete the task."
        }
    
    def invoke(self, messages, *args, **kwargs):
        """Invoke the model and ensure valid JSON output."""
        try:
            # Add system message for JSON formatting
            system_message = HumanMessage(content="""
You are a browser automation assistant. Always respond with valid JSON that follows this structure:
For navigation actions:
{
  "action": "navigate",
  "url": "https://example.com"
}

For finding information:
{
  "action": "find",
  "text": "The information that was found"
}

For completing a task:
{
  "action": "finish",
  "result": "Description of what was found or done"
}

Respond ONLY with valid JSON. Do not include any other text, markdown, or code formatting.
""")
            
            # Insert system message at the beginning if not already present
            if not any(isinstance(m, HumanMessage) and "valid JSON" in m.content for m in messages):
                messages = [system_message] + messages
            
            # Try to get a response from the model
            logger.debug(f"Sending {len(messages)} messages to LLM")
            response = self.chat_model.invoke(messages, *args, **kwargs)
            
            # Try to parse as JSON
            content = response.content
            logger.debug(f"Raw content from LLM: {content}")
            
            try:
                # First try: direct JSON parsing
                json_data = json.loads(content)
                logger.debug(f"LLM produced valid JSON response: {json_data}")
                return response
            except json.JSONDecodeError as e:
                logger.error(f"LLM produced invalid JSON: {content}")
                logger.error(f"JSON error: {str(e)}")
                
                # Try multiple extraction strategies
                extracted_json = self._extract_json_from_text(content)
                if extracted_json:
                    logger.debug(f"Successfully extracted JSON: {extracted_json}")
                    return AIMessage(content=json.dumps(extracted_json))
                
                # Return a fallback response if no valid JSON found
                content = json.dumps(self.default_fallback_msg)
                return AIMessage(content=content)
                
        except Exception as e:
            logger.error(f"Error invoking LLM: {str(e)}", exc_info=True)
            
            # Return a fallback response for any error
            content = json.dumps(self.default_fallback_msg)
            return AIMessage(content=content)
    
    def _extract_json_from_text(self, text):
        """Try multiple strategies to extract valid JSON from text."""
        import re
        
        # Strategy 1: Try to find JSON in code blocks
        json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_block_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Strategy 2: Try to find any JSON object in the text
        json_obj_pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})'
        matches = re.findall(json_obj_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Strategy 3: Try to fix common JSON formatting issues
        # Sometimes models add trailing commas or miss quotes around keys
        cleaned_text = text
        # Remove non-JSON text outside of curly braces
        json_content_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
        if json_content_match:
            cleaned_text = json_content_match.group(1)
        
        # Fix unquoted keys
        cleaned_text = re.sub(r'(\w+)(:)', r'"\1"\2', cleaned_text)
        # Fix trailing commas before closing braces
        cleaned_text = re.sub(r',(\s*})', r'\1', cleaned_text)
        # Fix multiple consecutive commas
        cleaned_text = re.sub(r',\s*,', ',', cleaned_text)
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass
        
        # If all strategies fail, return None
        return None

class DirectBrowser:
    """Direct browser controller that doesn't rely on browser-use's Agent.run method."""
    
    def __init__(self, use_fake_llm=False):
        """Initialize the DirectBrowser."""
        logger.debug("Initializing DirectBrowser")
        
        # Disable Playwright browser logs
        os.environ["DEBUG"] = ""  # Override the previous setting
        os.environ["PLAYWRIGHT_DRIVER_VERBOSE"] = "0"
        
        self._is_closed = False
        self.browser = None
        self.use_fake_llm = use_fake_llm
    
    async def _setup_browser(self):
        """Set up the browser instance."""
        if not self.browser:
            logger.debug("Creating browser instance")
            try:
                # Create browser instance with context and page
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-software-rasterizer',
                        '--disable-gpu-sandbox'
                    ]
                )
                context = await browser.new_context()
                page = await context.new_page()
                
                # Create a Browser instance and manually set its attributes
                self.browser = Browser()
                self.browser._browser = browser
                self.browser._playwright = playwright
                self.browser.page = page
                logger.debug("Browser instance created successfully with page")
            except Exception as e:
                logger.error(f"Error creating browser: {str(e)}", exc_info=True)
                raise
        
        # Ensure the page is created
        if not hasattr(self.browser, 'page') or self.browser.page is None:
            logger.debug("Page not initialized, creating new page")
            try:
                if hasattr(self.browser, '_browser') and self.browser._browser:
                    self.browser.page = await self.browser._browser.new_page()
                    logger.debug("New page created successfully")
                else:
                    logger.error("Cannot create page: browser not properly initialized")
            except Exception as e:
                logger.error(f"Error creating page: {str(e)}", exc_info=True)
        
        return self.browser
    
    async def _take_screenshot(self, filename=None):
        """Take a screenshot and save it with a timestamp."""
        if not self.browser or not hasattr(self.browser, 'page'):
            logger.error("Browser or page not initialized")
            return None

        # Generate a timestamp-based filename if none is provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"screenshot_{timestamp}.png"
        
        # Ensure the path is within the screenshots directory
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        
        logger.debug(f"Taking screenshot: {filepath}")
        try:
            await self.browser.page.screenshot(path=filepath)
            logger.debug(f"Screenshot saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}", exc_info=True)
            return None
    
    async def _take_screenshot_base64(self):
        """Take a screenshot and return it as base64 encoded string."""
        if not self.browser or not hasattr(self.browser, 'page'):
            logger.error("Browser or page not initialized")
            return None

        logger.debug("Taking screenshot as base64")
        try:
            # Take screenshot and return as base64
            screenshot_bytes = await self.browser.page.screenshot()
            import base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            logger.debug("Screenshot taken successfully as base64")
            return screenshot_base64
        except Exception as e:
            logger.error(f"Error taking screenshot as base64: {str(e)}", exc_info=True)
            return None
    
    async def _get_page_content(self):
        """Get the text content of the current page."""
        if not self.browser or not hasattr(self.browser, 'page'):
            logger.error("Browser or page not initialized")
            return ""
        
        logger.debug("Getting page content")
        try:
            content = await self.browser.page.content()
            # Could also use: await self.browser.page.evaluate("document.body.innerText")
            logger.debug(f"Page content retrieved (length: {len(content)})")
            return content
        except Exception as e:
            logger.error(f"Error getting page content: {str(e)}", exc_info=True)
            return ""
    
    async def navigate(self, url):
        """Navigate to a URL."""
        # Make sure browser is set up
        await self._setup_browser()
        
        logger.debug(f"Navigating to URL: {url}")
        try:
            # Directly access the page if available
            if hasattr(self.browser, 'page') and self.browser.page is not None:
                await self.browser.page.goto(url)
                await asyncio.sleep(2)  # Give page a moment to load
                current_url = self.browser.page.url
                logger.debug(f"Navigation successful to {url}, current URL: {current_url}")
                return True
            else:
                # Try to access the page through other methods
                if hasattr(self.browser, 'goto'):
                    await self.browser.goto(url)
                    logger.debug(f"Navigation successful using browser.goto")
                    return True
                elif hasattr(self.browser, '_browser') and self.browser._browser is not None:
                    # Create a new page and navigate
                    logger.debug("Creating new page for navigation")
                    self.browser.page = await self.browser._browser.new_page()
                    await self.browser.page.goto(url)
                    logger.debug(f"Navigation successful with new page")
                    return True
                else:
                    logger.error("No page object or navigation method available")
                    return False
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}", exc_info=True)
            return False
    
    async def close(self):
        """Close the browser."""
        if self._is_closed:
            return
        
        logger.debug("Closing browser")
        if self.browser:
            try:
                if hasattr(self.browser, 'page') and hasattr(self.browser.page, 'is_closed') and not self.browser.page.is_closed():
                    await self.browser.close()
                elif hasattr(self.browser, '_browser') and self.browser._browser.is_connected():
                    await self.browser._browser.close()
                logger.debug("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}", exc_info=True)
        
        self._is_closed = True
    
    def _get_llm(self):
        """Get an LLM instance (either fake or real)."""
        if self.use_fake_llm:
            logger.warning("!!! Using FakeListChatModel for testing instead of Ollama !!!")
            fake_responses = [
                AIMessage(content=json.dumps({"action": "navigate", "url": "https://example.com"})),
                AIMessage(content=json.dumps({"action": "finish", "result": "Navigated to example.com and finished."}))
            ]
            return FakeListChatModel(responses=fake_responses)
        else:
            logger.info("Using ChatOllama with llama3:8b model")
            try:
                # Configure the ChatOllama model
                chat_model = ChatOllama(
                    model="llama3:8b",
                    temperature=0.1,
                    # Tell Ollama to expect JSON output
                    format="json"
                )
                logger.debug("ChatOllama model initialized successfully")
                
                # Test the chat model with a simple prompt
                try:
                    test_prompt = "Respond with a simple JSON that has 'action' and 'url' fields"
                    logger.debug(f"Testing ChatOllama with prompt: {test_prompt}")
                    test_response = chat_model.invoke([HumanMessage(content=test_prompt)])
                    logger.debug(f"ChatOllama test response: {test_response.content}")
                except Exception as e:
                    logger.error(f"ChatOllama test failed: {str(e)}", exc_info=True)
                
                # Wrap the model to ensure valid JSON output
                logger.debug("Creating SafeJsonChatOllamaWrapper around ChatOllama")
                wrapper = SafeJsonChatOllamaWrapper(chat_model)
                logger.debug("SafeJsonChatOllamaWrapper created successfully")
                return wrapper
            except Exception as e:
                logger.error(f"Failed to initialize ChatOllama: {str(e)}", exc_info=True)
                logger.warning("Falling back to FakeListChatModel")
                # Fall back to fake model if Ollama fails
                fake_responses = [
                    AIMessage(content=json.dumps({"action": "navigate", "url": "https://example.com"})),
                    AIMessage(content=json.dumps({"action": "finish", "result": "Ollama failed to initialize. Using fake responses instead."}))
                ]
                return FakeListChatModel(responses=fake_responses)
    
    async def run_task(self, instruction: str, callbacks=None):
        """Run a task using either fake LLM or Ollama."""
        logger.debug(f"Running task with instruction: {instruction}")
        
        # Get LLM (either fake or real)
        llm = self._get_llm()
        
        # Set up browser
        await self._setup_browser()
        
        # Generate a unique session ID for this task
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Send initial screenshot if callbacks are provided
        initial_screenshot = await self._take_screenshot_base64()
        initial_screenshot_path = await self._take_screenshot(f"initial_{session_id}.png")
        if callbacks and "on_screenshot" in callbacks and initial_screenshot:
            callbacks["on_screenshot"](initial_screenshot, f"Initial state {initial_screenshot_path}")
        
        # Get first LLM response
        logger.debug("Getting first LLM response")
        response = llm.invoke([HumanMessage(content=instruction)])
        logger.debug(f"LLM response: {response}")
        
        try:
            # Parse the first response
            content = response.content
            action_data = json.loads(content)
            logger.debug(f"Parsed action: {action_data}")
            
            if callbacks and "on_progress" in callbacks:
                callbacks["on_progress"](f"Planning to {action_data['action']}")
            
            # Store message history
            message_history = [
                HumanMessage(content=instruction),
                AIMessage(content=content)  # First LLM response
            ]
            
            # Start the action loop - will continue as long as we have navigate actions
            navigation_count = 0
            current_action = action_data
            
            while current_action["action"] == "navigate" and navigation_count < 10:  # Limit to 10 steps to prevent infinite loops
                navigation_count += 1
                url = current_action["url"]
                logger.debug(f"Executing navigate action #{navigation_count} to {url}")
                
                if callbacks and "on_progress" in callbacks:
                    callbacks["on_progress"](f"Navigating to {url}")
                
                success = await self.navigate(url)
                
                if not success:
                    # Take screenshot of failed navigation
                    error_screenshot = await self._take_screenshot_base64()
                    error_screenshot_path = await self._take_screenshot(f"error_{session_id}_{navigation_count}.png")
                    if callbacks and "on_screenshot" in callbacks and error_screenshot:
                        callbacks["on_screenshot"](error_screenshot, f"Navigation failed {error_screenshot_path}")
                    
                    return f"Failed to navigate to the URL: {url}"
                
                # Navigation was successful
                # Take a screenshot and send it if callbacks are provided
                navigation_screenshot = await self._take_screenshot_base64()
                navigation_screenshot_path = await self._take_screenshot(f"navigation_{session_id}_{navigation_count}.png")
                if callbacks and "on_screenshot" in callbacks and navigation_screenshot:
                    callbacks["on_screenshot"](navigation_screenshot, f"Navigated to {url} {navigation_screenshot_path}")
                
                # Get page content for LLM
                page_content = await self._get_page_content()
                observation = f"Navigated to {url}. Page content: {page_content[:1000]}..."
                logger.debug(f"Getting LLM response with observation: {observation[:100]}...")
                
                if callbacks and "on_progress" in callbacks:
                    callbacks["on_progress"](f"Analyzing page content from {url}")
                
                # Add the observation to message history
                message_history.append(HumanMessage(content=observation))
                
                # Get next LLM response
                response = llm.invoke(message_history)
                logger.debug(f"LLM response after navigation #{navigation_count}: {response}")
                
                # Parse the response
                current_content = response.content
                current_action = json.loads(current_content)
                
                # Add the LLM response to message history
                message_history.append(AIMessage(content=current_content))
                
                # Take a screenshot after analysis
                analysis_screenshot = await self._take_screenshot_base64()
                analysis_screenshot_path = await self._take_screenshot(f"analysis_{session_id}_{navigation_count}.png")
                if callbacks and "on_screenshot" in callbacks and analysis_screenshot:
                    callbacks["on_screenshot"](analysis_screenshot, f"Analysis after navigation #{navigation_count} {analysis_screenshot_path}")
            
            # We've either reached a non-navigate action or hit the maximum number of steps
            if navigation_count >= 10 and current_action["action"] == "navigate":
                return f"Reached maximum navigation depth (10 steps). Last action was: {current_action['action']} to {current_action.get('url', 'unknown URL')}"
            
            # Handle the final action (either finish, find, or something else)
            if current_action["action"] == "finish":
                return f"Task completed after {navigation_count} navigation steps: {current_action['result']}"
            elif current_action["action"] == "find":
                # Handle find action
                text_to_find = current_action.get("text", "")
                if text_to_find:
                    return f"Found information after {navigation_count} navigation steps: {text_to_find}"
                else:
                    return f"Found something after {navigation_count} navigation steps but no text was provided"
            else:
                # Could implement other actions like click, type, etc.
                return f"Unhandled action after {navigation_count} navigation steps: {current_action['action']}"
                
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}", exc_info=True)
            # Take error screenshot
            error_screenshot = await self._take_screenshot_base64()
            error_screenshot_path = await self._take_screenshot(f"exception_{session_id}.png")
            if callbacks and "on_screenshot" in callbacks and error_screenshot:
                callbacks["on_screenshot"](error_screenshot, f"Error: {str(e)} {error_screenshot_path}")
            return f"Error: {str(e)}"
    
    def execute(self, instruction: str, callbacks: Optional[Dict[str, Callable]] = None) -> str:
        """Execute a task with the given instruction."""
        logger.debug(f"Executing task: {instruction}")
        
        try:
            # Create new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the task
            result = loop.run_until_complete(self.run_task(instruction, callbacks))
            logger.debug(f"Task execution completed: {result}")
            
            if callbacks and "on_progress" in callbacks:
                callbacks["on_progress"]("Task completed")
                
            return result
            
        except Exception as e:
            logger.error(f"Error in execute: {str(e)}", exc_info=True)
            return f"Failed to execute task: {str(e)}"
        finally:
            # Close the browser
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.close())
            loop.close()
    
    def __del__(self):
        """Clean up on destruction."""
        logger.debug("DirectBrowser.__del__ called")
        if not self._is_closed and self.browser:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.close())
            loop.close()

def create_direct_browser(use_fake_llm=False):
    """Create and return a DirectBrowser instance."""
    logger.info(f"Creating DirectBrowser instance (use_fake_llm={use_fake_llm})")
    return DirectBrowser(use_fake_llm=use_fake_llm) 
