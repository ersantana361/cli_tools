#!/usr/bin/env python3
"""
claude_integrated_pr_review.py - Enhanced version that can be called by Claude CLI

This script can be executed directly by Claude CLI when you ask it to review PRs.
"""

import sys
import logging

# Direct imports - will fail immediately if dependencies are missing
from github import Github
import requests
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Handle import from different locations (direct execution vs import from mcp/)
try:
    from pr_reviewer import ClaudeIntegratedPRReviewer
except ImportError:
    # If importing from mcp/ subdirectory, try parent directory
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    from pr_reviewer import ClaudeIntegratedPRReviewer

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function for Claude CLI integration"""
    logger.info("🎬 Starting Claude Integrated PR Review Tool...")
    
    try:
        reviewer = ClaudeIntegratedPRReviewer()
        
        if len(sys.argv) > 1:
            # Direct command line usage
            user_input = " ".join(sys.argv[1:])
            logger.info("📝 Command line input detected")
        else:
            # Read from stdin (Claude CLI usage)
            logger.info("📝 Reading from stdin...")
            user_input = sys.stdin.read().strip()
        
        logger.debug(f"📝 User input: {user_input}")
        
        if not user_input:
            usage_msg = """Usage: echo 'review PR 123' | python claude_integrated_pr_review.py
   or: python claude_integrated_pr_review.py 'review PR 123'"""
            print(usage_msg)
            logger.info("❌ No input provided")
            return
        
        response = reviewer.handle_claude_request(user_input)
        print(response)
        logger.info("🎬 Program completed")
        
    except Exception as e:
        error_msg = f"Fatal error: {str(e)}"
        logger.error(f"💥 {error_msg}")
        print(f"💥 {error_msg}")
        
        import traceback
        logger.error("🔍 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
