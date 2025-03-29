import argparse
import logging
from raw_ollama import create_raw_ollama_browser

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run a sample task with the DirectOllamaBrowser."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run browser agent with direct Ollama API integration")
    parser.add_argument("--fake", action="store_true", help="Use fake responses instead of querying Ollama")
    parser.add_argument("--instruction", type=str, default="Go to example.com and tell me what's on the page",
                       help="Instruction to give to the agent")
    args = parser.parse_args()
    
    logger.info(f"Creating DirectOllamaBrowser (fake_responses={args.fake})")
    browser_agent = create_raw_ollama_browser(use_fake_responses=args.fake)
    
    try:
        logger.info(f"Running instruction: {args.instruction}")
        
        result = browser_agent.execute(args.instruction)
        
        logger.info("Task completed")
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 
