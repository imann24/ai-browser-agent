import os
import json
import asyncio
import logging
import requests
from typing import Dict, Any, List, Optional, Callable

# Import browser functionality directly
from browser_use import Browser

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('raw_ollama.log')
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Enable Playwright debug logging
os.environ["DEBUG"] = "pw:api,pw:browser"
os.environ["PLAYWRIGHT_DRIVER_VERBOSE"] = "1"

class DirectOllamaBrowser:
    """Direct browser controller using raw Ollama API requests instead of LangChain."""
    
    def __init__(self, use_fake_responses=False):
        """Initialize the DirectOllamaBrowser."""
        logger.debug("Initializing DirectOllamaBrowser")
        self._is_closed = False
        self.browser = None
        self.use_fake_responses = use_fake_responses
        self.ollama_base_url = "http://localhost:11434"
    
    async def _setup_browser(self):
        """Set up the browser instance."""
        if not self.browser:
            logger.debug("Creating browser instance")
            self.browser = Browser()
            logger.debug("Browser instance created")
        return self.browser
    
    async def _take_screenshot(self, filename="screenshot.png"):
        """Take a screenshot and save it."""
        if not self.browser or not hasattr(self.browser, 'page'):
            logger.error("Browser or page not initialized")
            return

        logger.debug(f"Taking screenshot: {filename}")
        try:
            await self.browser.page.screenshot(path=filename)
            logger.debug("Screenshot taken successfully")
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}", exc_info=True)
    
    async def _get_page_content(self):
        """Get the text content of the current page."""
        if not self.browser or not hasattr(self.browser, 'page'):
            logger.error("Browser or page not initialized")
            return ""
        
        logger.debug("Getting page content")
        try:
            content = await self.browser.page.content()
            # Get just the text content (cleaner for LLM)
            text_content = await self.browser.page.evaluate("document.body.innerText")
            logger.debug(f"Page text content retrieved (length: {len(text_content)})")
            return text_content
        except Exception as e:
            logger.error(f"Error getting page content: {str(e)}", exc_info=True)
            return ""
    
    async def navigate(self, url):
        """Navigate to a URL."""
        if not self.browser or not hasattr(self.browser, 'page'):
            logger.error("Browser or page not initialized")
            return False
        
        logger.debug(f"Navigating to URL: {url}")
        try:
            await self.browser.page.goto(url)
            await asyncio.sleep(2)  # Give page a moment to load
            current_url = self.browser.page.url
            logger.debug(f"Navigation complete. Current URL: {current_url}")
            return True
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
    
    def _query_ollama(self, prompt, system_prompt=None):
        """Query Ollama API directly instead of using langchain."""
        if self.use_fake_responses:
            logger.warning("Using fake responses instead of querying Ollama")
            return {"action": "navigate", "url": "https://example.com"}
        
        try:
            logger.debug(f"Querying Ollama with prompt: {prompt[:100]}...")
            
            # Prepare the request
            data = {
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 100
                },
                "format": "json"  # Request JSON format
            }
            
            # Add system prompt if provided
            if system_prompt:
                data["system"] = system_prompt
                
            # Make the request to Ollama
            logger.debug("Sending request to Ollama API")
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=data
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {"action": "finish", "result": "Error querying Ollama"}
            
            # Get the response content
            response_data = response.json()
            content = response_data.get("response", "")
            logger.debug(f"Ollama raw response: {content}")
            
            # Try to parse as JSON
            try:
                # Direct parsing attempt
                json_data = json.loads(content)
                logger.debug(f"Successfully parsed JSON response: {json_data}")
                return json_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                
                # Try multiple extraction approaches
                extracted_json = self._extract_json_from_text(content)
                if extracted_json:
                    logger.debug(f"Extracted valid JSON using advanced methods: {extracted_json}")
                    return extracted_json
                
                # Fallback to a default response
                return {"action": "finish", "result": "Could not parse response from Ollama"}
                
        except Exception as e:
            logger.error(f"Error querying Ollama: {str(e)}", exc_info=True)
            return {"action": "finish", "result": f"Error: {str(e)}"}
            
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
    
    async def run_task(self, instruction: str):
        """Run a task using Ollama."""
        logger.debug(f"Running task with instruction: {instruction}")
        
        # Set up browser
        await self._setup_browser()
        
        # System prompt instructing JSON response format
        system_prompt = """
You are a browser automation assistant. Your task is to help the user navigate websites by providing actions.
ALWAYS respond with ONLY a valid JSON object that follows this structure:

For navigation: 
{
  "action": "navigate",
  "url": "https://example.com"
}

For completing a task: 
{
  "action": "finish",
  "result": "Description of what was found or done"
}

DO NOT include explanations, markdown formatting, or code blocks around your response.
Your response must ONLY be a valid JSON object with no additional text.
"""
        
        # Initial query to Ollama
        logger.debug("Getting first action from Ollama")
        action_data = self._query_ollama(instruction, system_prompt)
        
        try:
            logger.debug(f"Initial action: {action_data}")
            
            if action_data.get("action") == "navigate":
                url = action_data.get("url")
                logger.debug(f"Executing navigate action to {url}")
                success = await self.navigate(url)
                
                if success:
                    # Take a screenshot
                    await self._take_screenshot(filename="navigation_result.png")
                    
                    # Get page content
                    page_content = await self._get_page_content()
                    observation = f"Navigated to {url}. Here's what I found on the page:\n\n{page_content[:1500]}..."
                    
                    # Query Ollama again with the observation
                    logger.debug("Getting second action from Ollama")
                    prompt = f"{instruction}\n\nI've {observation}"
                    final_action = self._query_ollama(prompt, system_prompt)
                    
                    logger.debug(f"Final action: {final_action}")
                    
                    if final_action.get("action") == "finish":
                        return f"Task completed: {final_action.get('result', 'No result provided')}"
                    else:
                        return f"Unexpected final action: {final_action.get('action', 'No action specified')}"
                else:
                    return "Failed to navigate to the URL."
            else:
                return f"Unexpected first action: {action_data.get('action', 'No action specified')}"
                
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"
    
    def execute(self, instruction: str, callbacks: Optional[Dict[str, Callable]] = None) -> str:
        """Execute a task with the given instruction."""
        logger.debug(f"Executing task: {instruction}")
        
        try:
            # Create new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the task
            result = loop.run_until_complete(self.run_task(instruction))
            logger.debug(f"Task execution completed: {result}")
            
            if callbacks and "on_progress" in callbacks:
                callbacks["on_progress"]("Task completed")
                
            return result
            
        except Exception as e:
            logger.error(f"Error in execute: {str(e)}", exc_info=True)
            return f"Failed to execute task: {str(e)}"
        finally:
            # Clean up resources
            try:
                # Close the browser
                if loop and not loop.is_closed():
                    loop.run_until_complete(self.close())
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
            finally:
                if loop and not loop.is_closed():
                    loop.close()
    
    def __del__(self):
        """Clean up on destruction."""
        logger.debug("DirectOllamaBrowser.__del__ called")
        if not self._is_closed and self.browser:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.close())
                loop.close()
            except Exception as e:
                logger.error(f"Error in __del__: {str(e)}", exc_info=True)

def create_raw_ollama_browser(use_fake_responses=False):
    """Create and return a DirectOllamaBrowser instance."""
    logger.info(f"Creating DirectOllamaBrowser instance (use_fake_responses={use_fake_responses})")
    return DirectOllamaBrowser(use_fake_responses=use_fake_responses) 
