import os
import asyncio
import logging
import json
from typing import Dict, Any, Callable, Optional, List, Union
from browser_use import Browser, Agent
import ollama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
# Remove BaseChatModel and related imports if no longer needed elsewhere
# from langchain_core.language_models.chat_models import BaseChatModel 
from langchain_core.outputs import ChatResult, ChatGeneration, LLMResult
# from langchain_core.callbacks.manager import CallbackManagerForLLMRun

# Import the official LangChain Ollama integration
from langchain_ollama.chat_models import ChatOllama
# Import FakeListChatModel for testing
from langchain_community.chat_models.fake import FakeListChatModel 
from langchain_core.runnables import RunnableConfig # Needed for invoke signature
from langchain_core.language_models import BaseChatModel # For wrapper typing
# Import callback handler base
from langchain_core.callbacks.base import BaseCallbackHandler

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('browser_agent.log')
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Enable Playwright debug logging through environment variables
os.environ["DEBUG"] = "pw:api,pw:browser"
os.environ["PLAYWRIGHT_DRIVER_VERBOSE"] = "1"
# Enable LangChain verbose logging
os.environ["LANGCHAIN_VERBOSE"] = "true"

def check_ollama_health():
    """Check if Ollama is running and accessible."""
    try:
        logger.debug("=== Starting Ollama Health Check ===")
        models = ollama.list()
        logger.debug(f"Available Ollama models: {models}")
        return True
    except Exception as e:
        logger.error(f"Ollama health check failed: {str(e)}", exc_info=True)
        return False

# --- Define Custom Callback Handler ---
class MyAgentCallbackHandler(BaseCallbackHandler):
    """Simple callback handler to log agent actions and other events."""
    
    def on_agent_action(self, action, **kwargs: Any) -> Any:
        """Run on agent action."""
        logger.debug(f"CALLBACK: Agent Action: {action}")

    def on_agent_finish(self, finish, **kwargs: Any) -> Any:
        """Run on agent end."""
        logger.debug(f"CALLBACK: Agent Finish: {finish}")

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""
        logger.debug(f"CALLBACK: LLM Start with prompts: {prompts}")

    def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        """Run when Chat Model starts running."""
        logger.debug(f"CALLBACK: Chat Model Start with messages: {messages}")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        logger.debug(f"CALLBACK: Tool Start: {serialized.get('name')}, Input: {input_str}")

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        logger.debug(f"CALLBACK: Tool End with output: {output}")
        
    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        """Run when tool errors."""
        logger.error(f"CALLBACK: Tool Error: {error}", exc_info=True)

# --- End Custom Callback Handler ---

# --- Define the Safe JSON Wrapper ---
class SafeJsonChatOllamaWrapper(BaseChatModel):
    """Wraps a BaseChatModel to ensure its output content is valid JSON."""
    chat_model: BaseChatModel
    
    def __init__(self, chat_model: BaseChatModel, **kwargs: Any):
        # Need to call super().__init__() properly, passing necessary args if BaseChatModel requires them.
        # For now, let's assume BaseChatModel's default init is sufficient or handled by Langchain's mechanisms.
        # We store the model instance directly.
        # Pass chat_model and any other kwargs to the superclass init
        # Pydantic V2 often expects fields via keyword arguments in super().__init__
        super().__init__(chat_model=chat_model, **kwargs)
        # The line below might be redundant now, as super().__init__ should handle setting the field
        # self.chat_model = chat_model 
        logger.debug("SafeJsonChatOllamaWrapper initialized.")

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

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None, # Using Any for simplicity
        **kwargs: Any,
    ) -> LLMResult:
        """Call the wrapped model and validate/fix JSON output."""
        logger.debug(f"SafeJsonWrapper: Calling wrapped model _generate with {len(messages)} messages.")
        llm_result = self.chat_model._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        logger.debug("SafeJsonWrapper: Received result from wrapped model.")

        for generation_list in llm_result.generations:
            for generation in generation_list:
                if hasattr(generation, 'message') and hasattr(generation.message, 'content'):
                    content = generation.message.content
                    logger.debug(f"SafeJsonWrapper: Original content: {content}")
                    try:
                        # Attempt to parse the content as JSON
                        json.loads(content)
                        logger.debug("SafeJsonWrapper: Content is valid JSON.")
                    except json.JSONDecodeError:
                        logger.warning(f"SafeJsonWrapper: LLM response is not valid JSON: '{content}'")
                        
                        # Try to extract JSON using our helper method
                        extracted_json = self._extract_json_from_text(content)
                        if extracted_json:
                            # If we successfully extracted JSON, use it
                            fixed_content = json.dumps(extracted_json)
                            logger.debug(f"SafeJsonWrapper: Successfully extracted JSON: {fixed_content}")
                            generation.message.content = fixed_content
                        else:
                            # Fall back to default if extraction failed
                            fallback_content = json.dumps({
                                "action": "finish",
                                "result": f"LLM response was not valid JSON. Original response: {content}"
                            })
                            generation.message.content = fallback_content
                            logger.warning(f"SafeJsonWrapper: Replaced content with fallback: {fallback_content}")
                    except TypeError:
                         logger.warning(f"SafeJsonWrapper: Content was not a string or bytes-like object: {type(content)}. Skipping JSON check.")
                         # Optionally handle non-string content if necessary
                         pass # Assuming content should ideally be string for JSON parsing

        return llm_result

    # Implement other necessary abstract methods if any (e.g., _llm_type)
    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "safe_json_chat_ollama_wrapper"

# --- End Define the Safe JSON Wrapper ---

def create_browser_agent():
    """Create a browser agent instance that leverages Ollama for LLM capabilities."""
    logger.debug("=== Starting Browser Agent Creation ===")
    if not check_ollama_health():
        raise RuntimeError("Ollama is not running or not accessible. Please ensure Ollama is installed and running.")
    
    # Set default model permanently
    model_name = 'llama3:8b'
    logger.debug(f"Using Ollama model: {model_name}")
    
    # Use ChatOllama with the real Ollama model
    try:
        logger.debug(f"Creating ChatOllama with model: {model_name}")
        ollama_chat_model = ChatOllama(
            model=model_name,
            temperature=0.1
        )
        logger.debug("ChatOllama model created successfully")
        
        # Wrap the model for safe JSON handling
        logger.debug("Creating SafeJsonChatOllamaWrapper around ChatOllama")
        safe_ollama_chat_model = SafeJsonChatOllamaWrapper(chat_model=ollama_chat_model)
        logger.debug("SafeJsonChatOllamaWrapper created successfully")
        
        # Test the real model
        try:
            # Use a simple test message
            test_result = safe_ollama_chat_model.invoke([HumanMessage(content="Give me a simple JSON with action navigate to Google")])
            logger.debug(f"Test generation successful (real model): {test_result}")
            # We'll use the real model
            llm_to_pass_to_agent = safe_ollama_chat_model
        except Exception as e:
            logger.error(f"Test generation with real model failed: {str(e)}", exc_info=True)
            logger.warning("Falling back to fake model")
            # Fall back to fake model if test fails
            fake_responses = [
                AIMessage(content=json.dumps({"action": "navigate", "url": "https://example.com"})),
                AIMessage(content=json.dumps({"action": "finish", "result": "Navigated to example.com and finished."}))
            ]
            fake_llm = FakeListChatModel(responses=fake_responses)
            logger.warning(f"Using FakeListChatModel with predefined responses: {fake_responses}")
            llm_to_pass_to_agent = fake_llm
    except Exception as e:
        logger.error(f"Error creating real model: {str(e)}", exc_info=True)
        logger.warning("Falling back to fake model")
        # Fall back to fake model if creation fails
        fake_responses = [
            AIMessage(content=json.dumps({"action": "navigate", "url": "https://example.com"})),
            AIMessage(content=json.dumps({"action": "finish", "result": "Navigated to example.com and finished."}))
        ]
        fake_llm = FakeListChatModel(responses=fake_responses)
        logger.warning(f"Using FakeListChatModel with predefined responses: {fake_responses}")
        llm_to_pass_to_agent = fake_llm
    
    # Create persistent browser instance
    logger.debug("Creating persistent browser instance")
    try:
        browser_instance = Browser()
        logger.debug("Browser instance created successfully")
    except Exception as e:
        logger.error(f"Error creating browser: {str(e)}", exc_info=True)
        raise
    
    class BrowserAgentWrapper:
        def __init__(self):
            logger.debug("=== Initializing BrowserAgentWrapper ===")
            # Restore browser instance management
            self.browser = browser_instance 
            self._is_closed = False # Keep track if close has been called
            self._current_agent = None # Keep agent reference if needed for closing?
            logger.debug("BrowserAgentWrapper initialized (with persistent browser)")
        
        def execute(self, instruction: str, callbacks: Optional[Dict[str, Callable]] = None) -> str:
            logger.debug(f"=== Starting execution with instruction: {instruction} ===")
            loop = None # Keep loop variable
            try:
                logger.debug("Creating new event loop")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Agent creation now happens in setup_context using self.browser
                current_agent_local = None 
                
                try:
                    # Pass self.browser to setup_context
                    async def setup_context(persistent_browser):
                        logger.debug("Entering setup_context")
                        try:
                            logger.debug("Creating agent with persistent browser instance")
                            logger.debug(f"Pre-Agent Init: Browser object: {persistent_browser}")
                            logger.debug(f"Pre-Agent Init: Browser page: {getattr(persistent_browser, 'page', 'N/A')}")
                            logger.debug(f"Pre-Agent Init: LLM object: {llm_to_pass_to_agent}")
                            logger.debug(f"Pre-Agent Init: Instruction: {instruction}")
                            logger.debug(f"LLM model (fake): {llm_to_pass_to_agent}") 
                            
                            # Create the agent using the raw instruction and the persistent browser.
                            # Instantiate the callback handler
                            # handler = MyAgentCallbackHandler()
                            # logger.debug("Instantiated MyAgentCallbackHandler")
                            
                            agent_instance = Agent(
                                task=instruction, # Pass raw instruction
                                browser=persistent_browser, # Use the persistent browser instance
                                llm=llm_to_pass_to_agent, # Pass the FAKE model
                                # callbacks=[handler] # REMOVED: Not supported by Agent constructor
                            )
                            logger.debug("Agent created successfully")
                            
                            # Test the agent's LLM using a simple test call.
                            try:
                                test_message = HumanMessage(content="test")
                                test_result = agent_instance.llm.invoke([test_message])
                                logger.debug(f"Agent LLM test successful (via fake model): {test_result}")
                            except Exception as e:
                                logger.error(f"Agent LLM test failed (via fake model): {str(e)}", exc_info=True) # Added exc_info
                                raise
                            
                            logger.debug("Exiting setup_context")
                            return agent_instance # Return the created agent
                        except Exception as e:
                            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
                            raise

                    logger.debug("Running setup_context")
                    # Pass the persistent self.browser to setup_context
                    current_agent_local = loop.run_until_complete(setup_context(self.browser))
                    # Store agent reference on self if needed for close?
                    # self._current_agent = current_agent_local 
                    logger.debug("Agent setup completed")

                    async def run_agent(agent_to_run):
                        logger.debug("Entering run_agent")
                        # Restore max_steps argument
                        max_agent_steps = 50 
                        logger.debug(f"Calling agent.run with max_steps={max_agent_steps}")
                        agent_history_result = await agent_to_run.run(max_steps=max_agent_steps)
                        logger.debug(f"agent.run completed. Raw result type: {type(agent_history_result)}")
                        logger.debug(f"agent.run result: {agent_history_result}")
                        logger.debug("Exiting run_agent")
                        return str(agent_history_result)

                    logger.debug("Starting agent execution with 180 second timeout") 
                    result = loop.run_until_complete(
                        asyncio.wait_for(run_agent(current_agent_local), timeout=180) 
                    )
                    logger.debug(f"Agent execution completed successfully. Final result: {result}")
                    if callbacks and "on_progress" in callbacks:
                        callbacks["on_progress"]("Task completed")
                    return str(result)
                    
                except asyncio.TimeoutError:
                    logger.warning("Agent execution timed out after 180 seconds")
                    if callbacks and "on_progress" in callbacks:
                        callbacks["on_progress"]("Task timed out after 180 seconds")
                    return "The operation timed out. The agent was taking too long to complete the task."
                finally:
                     # Clear agent reference after execution if stored
                     # if self._current_agent:
                     #    self._current_agent = None
                    pass # No specific cleanup needed here now
                
            except Exception as e:
                logger.error("Error in execution: %s", str(e), exc_info=True) 
                raise 
            finally:
                # Browser is persistent, close it only in BrowserAgentWrapper.close()
                # Close the main loop for this execution
                if loop:
                    logger.debug("Closing execution event loop.")
                    loop.close()
                logger.debug("Execution finished.")
        
        def close(self):
             # Restore closing logic for persistent browser
            if not self._is_closed:
                logger.debug("Closing BrowserAgentWrapper and persistent browser instance.")
                try:
                    # Use asyncio for closing the persistent browser
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        # Close the main browser instance if it exists and is managed by the wrapper
                        if hasattr(self, 'browser') and self.browser:
                             if hasattr(self.browser, 'page') and hasattr(self.browser.page, 'is_closed') and not self.browser.page.is_closed():
                                logger.debug("Attempting to close browser page and context...")
                                loop.run_until_complete(self.browser.close())
                             elif hasattr(self.browser, '_browser') and self.browser._browser.is_connected():
                                logger.debug("Page already closed, attempting to close browser process...")
                                loop.run_until_complete(self.browser._browser.close())
                             else:
                                logger.debug("Browser or page already closed or not initialized.")
                        
                        # Clear agent reference if necessary (though agent uses the shared browser)
                        self._current_agent = None 
                        
                        self._is_closed = True
                        logger.debug("Persistent browser instance closing process completed.")
                    except Exception as e:
                        logger.error(f"Error during persistent browser close operation: {str(e)}", exc_info=True)
                    finally:
                        logger.debug("Closing asyncio loop for persistent browser close.")
                        loop.close()
                except Exception as e:
                    logger.error(f"Error setting up/tearing down asyncio loop for persistent browser close: {str(e)}", exc_info=True)
        
        def __del__(self):
            logger.debug("BrowserAgentWrapper.__del__ called")
            self.close() 
    
    logger.info("Creating and returning BrowserAgentWrapper instance")
    return BrowserAgentWrapper()
