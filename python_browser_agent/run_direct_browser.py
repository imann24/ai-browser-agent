import argparse
import logging
from direct_browser import create_direct_browser

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run a sample task with the DirectBrowser."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run browser agent with direct browser control")
    parser.add_argument("--fake-llm", action="store_true", help="Use fake LLM instead of Ollama")
    parser.add_argument("--instruction", type=str, default="Go to example.com and tell me what's on the page",
                       help="Instruction to give to the agent")
    args = parser.parse_args()
    
    logger.info(f"Creating DirectBrowser agent (fake_llm={args.fake_llm})")
    browser_agent = create_direct_browser(use_fake_llm=args.fake_llm)
    
    try:
        logger.info(f"Running instruction: {args.instruction}")
        
        result = browser_agent.execute(args.instruction)
        
        logger.info("Task completed")
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
    finally:
        # Clean up
        logger.info("Closing browser agent")
        browser_agent._is_closed = False  # Force cleanup to run
        del browser_agent

if __name__ == "__main__":
    main() 
