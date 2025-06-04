"""
Main PR reviewer class that orchestrates the review process.
"""

import os
import re
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

from .github_api import GitHubAPI
from .llm_analyzer import LLMAnalyzer
from .models import ReviewComment

logger = logging.getLogger(__name__)

class ClaudeIntegratedPRReviewer:
    """Enhanced PR reviewer that can parse natural language commands"""
    
    def __init__(self):
        logger.info("🚀 Initializing Claude Integrated PR Reviewer...")
        
        self.config_file = Path(".claude_pr_config.json")
        logger.debug(f"📁 Config file path: {self.config_file.absolute()}")
        
        self.default_config = {
            "max_comments": 8,
            "comment_delay": 2,
            "default_review_type": "categorized",
            "auto_dry_run": True,
            "confirmation_required": True,
            "llm_provider": "anthropic"
        }
        
        try:
            self.github_api = GitHubAPI()
            logger.info("✅ PR Reviewer initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize PR Reviewer: {e}")
            raise
        
    def load_config(self) -> dict:
        """Load configuration from file or use defaults"""
        logger.info("⚙️ Loading configuration...")
        
        if self.config_file.exists():
            logger.info(f"📁 Found config file: {self.config_file}")
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config = {**self.default_config, **file_config}
                    logger.info("✅ Configuration loaded from file")
                    logger.debug(f"📋 Config: {json.dumps(config, indent=2)}")
                    return config
            except Exception as e:
                logger.warning(f"⚠️ Could not load config file: {e}")
                logger.info("📋 Using default configuration")
        else:
            logger.info("📋 No config file found, using defaults")
            
        logger.debug(f"📋 Default config: {json.dumps(self.default_config, indent=2)}")
        return self.default_config
    
    def parse_natural_language_command(self, text: str) -> dict:
        """Parse natural language PR review commands"""
        logger.info("🔍 Parsing natural language command...")
        logger.debug(f"📝 Input text: {text}")
        
        command = {
            "pr_number": None,
            "repo_name": None,
            "review_type": "categorized",
            "dry_run": True,
            "confirmed": False
        }
        
        # Extract PR number
        logger.debug("🔍 Looking for PR number...")
        pr_patterns = [
            r'(?:PR|pr|pull request|pull-request)\s*#?(\d+)',
            r'#(\d+)',
            r'number\s+(\d+)',
            r'PR\s+(\d+)'
        ]
        
        for i, pattern in enumerate(pr_patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                command["pr_number"] = int(match.group(1))
                logger.info(f"✅ Found PR number: {command['pr_number']} (pattern {i+1})")
                break
        
        if not command["pr_number"]:
            logger.warning("⚠️ No PR number found in command")
        
        # Extract repository name (owner/repo format)
        logger.debug("🔍 Looking for repository name...")
        repo_patterns = [
            r'(?:repo|repository)\s+([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)',
            r'github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)',
            r'([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)'
        ]
        
        for i, pattern in enumerate(repo_patterns):
            match = re.search(pattern, text)
            if match and '/' in match.group(1):
                command["repo_name"] = match.group(1)
                logger.info(f"✅ Found repository: {command['repo_name']} (pattern {i+1})")
                break
        
        if not command["repo_name"]:
            logger.warning("⚠️ No repository name found in command")
        
        # Determine review type
        logger.debug("🔍 Determining review type...")
        if re.search(r'security|vulnerability|vulnerabilities|secure', text, re.IGNORECASE):
            command["review_type"] = "security"
            logger.info("✅ Review type: security")
        elif re.search(r'performance|speed|optimization|efficiency', text, re.IGNORECASE):
            command["review_type"] = "performance"
            logger.info("✅ Review type: performance")
        elif re.search(r'maintainability|maintenance|refactor|clean', text, re.IGNORECASE):
            command["review_type"] = "maintainability"
            logger.info("✅ Review type: maintainability")
        elif re.search(r'file.*by.*file|files.*separately|each.*file', text, re.IGNORECASE):
            command["review_type"] = "files"
            logger.info("✅ Review type: files")
        elif re.search(r'summary.*only|just.*summary|overview', text, re.IGNORECASE):
            command["review_type"] = "summary"
            logger.info("✅ Review type: summary")
        elif re.search(r'all.*types|complete|comprehensive|everything', text, re.IGNORECASE):
            command["review_type"] = "all"
            logger.info("✅ Review type: all")
        else:
            logger.info("✅ Review type: categorized (default)")
        
        # Check for dry run override
        logger.debug("🔍 Checking for dry run override...")
        if re.search(r'actually.*post|really.*post|for.*real|no.*dry', text, re.IGNORECASE):
            command["dry_run"] = False
            command["confirmed"] = True
            logger.info("✅ Dry run disabled - will actually post comments")
        else:
            logger.info("✅ Dry run enabled (default)")
        
        logger.info("✅ Command parsing completed")
        logger.debug(f"📋 Parsed command: {json.dumps(command, indent=2)}")
        
        return command
    
    def execute_review(self, command: dict) -> bool:
        """Execute the PR review based on parsed command"""
        logger.info("🚀 Starting PR review execution...")
        logger.debug(f"📋 Command: {json.dumps(command, indent=2)}")
        
        if not command["pr_number"]:
            error_msg = "No PR number found in the request"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            return False
        
        # Use default repo if not specified
        repo_name = command.get("repo_name")
        if not repo_name:
            logger.info("🔍 No repository specified, trying to detect from current directory...")
            repo_name = self._get_default_repo()
            if not repo_name:
                error_msg = "No repository specified. Use format: 'review PR 123 in owner/repo'"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                return False
            else:
                logger.info(f"✅ Auto-detected repository: {repo_name}")
        
        config = self.load_config()
        
        try:
            print(f"🤖 Starting PR review for #{command['pr_number']} in {repo_name}")
            print(f"📋 Review type: {command['review_type']}")
            print(f"🔍 Dry run: {'Yes' if command['dry_run'] else 'No'}")
            
            logger.info(f"🎯 Target: PR #{command['pr_number']} in {repo_name}")
            logger.info(f"📋 Review type: {command['review_type']}")
            logger.info(f"🔍 Dry run: {command['dry_run']}")
            
            # Get PR information
            print("📥 Fetching PR information...")
            pr_info = self.github_api.get_pr_info(repo_name, command["pr_number"])
            print(f"   📋 Title: {pr_info['title']}")
            print(f"   👤 Author: {pr_info['author']}")
            print(f"   📁 Files changed: {pr_info['files_changed']}")
            print(f"   ➕ Additions: +{pr_info['additions']}")
            print(f"   ➖ Deletions: -{pr_info['deletions']}")
            
            # Get PR diff
            print("📄 Fetching PR diff...")
            diff = self.github_api.get_pr_diff(repo_name, command["pr_number"])
            print(f"   📊 Diff size: {len(diff)} characters")
            
            # Analyze with LLM
            print("🧠 Analyzing with AI...")
            analyzer = LLMAnalyzer(provider=config.get("llm_provider", "anthropic"))
            analysis = analyzer.analyze_pr_diff(diff, pr_info, command["review_type"])
            
            # Display analysis
            print("\n" + "="*60)
            print("🔍 PR REVIEW ANALYSIS")
            print("="*60)
            print(analysis)
            print("="*60)
            
            # Generate and post comments for ALL review types (not just "files" and "all")
            print("\n💬 Generating actionable review comments...")
            
            # Get file list for intelligent comment generation
            files = self.github_api.get_pr_files(repo_name, command["pr_number"])
            
            # Use LLM to generate targeted, actionable comments
            comments = analyzer.generate_actionable_comments(diff, pr_info, files, command["review_type"])
            
            if comments:
                logger.info(f"✅ Generated {len(comments)} actionable comments")
                print(f"   📝 Generated {len(comments)} targeted comments")
                
                success = self.github_api.post_review_comments(
                    repo_name, command["pr_number"], comments, command["dry_run"]
                )
                if not success and not command["dry_run"]:
                    logger.error("❌ Failed to post comments")
                    return False
            else:
                print("ℹ️ No specific comments generated - analysis provided above")
            
            print(f"\n✅ Review completed successfully!")
            logger.info("✅ PR review execution completed successfully")
            
            if command["dry_run"]:
                print(f"\n💡 This was a dry run. To actually post comments, say:")
                print(f"   'Actually post the review for PR {command['pr_number']} in {repo_name}'")
            
            return True
            
        except Exception as e:
            error_msg = f"Error during review: {str(e)}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            
            # Print detailed traceback for debugging
            import traceback
            logger.error("🔍 Full traceback:")
            traceback.print_exc()
            return False
    
    def _get_default_repo(self) -> Optional[str]:
        """Try to determine default repository from current directory"""
        logger.info("🔍 Trying to auto-detect repository from git remote...")
        
        try:
            logger.debug("📡 Running: git remote get-url origin")
            
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"], 
                capture_output=True, text=True, cwd="."
            )
            
            logger.debug(f"📡 Git command return code: {result.returncode}")
            logger.debug(f"📡 Git command stdout: {result.stdout}")
            logger.debug(f"📡 Git command stderr: {result.stderr}")
            
            if result.returncode == 0:
                url = result.stdout.strip()
                logger.debug(f"✅ Git origin URL: {url}")
                
                # Parse GitHub URL
                if "github.com" in url:
                    if url.startswith("git@"):
                        # git@github.com:owner/repo.git
                        match = re.search(r'github\.com:([^/]+/[^.]+)', url)
                        logger.debug("🔍 Parsing SSH format URL")
                    else:
                        # https://github.com/owner/repo.git
                        match = re.search(r'github\.com/([^/]+/[^.]+)', url)
                        logger.debug("🔍 Parsing HTTPS format URL")
                    
                    if match:
                        repo = match.group(1).replace('.git', '')
                        logger.info(f"✅ Auto-detected repository: {repo}")
                        return repo
                    else:
                        logger.warning("⚠️ Could not parse GitHub URL")
                else:
                    logger.warning("⚠️ Git origin is not a GitHub URL")
            else:
                logger.warning("⚠️ Git command failed - probably not in a git repository")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to auto-detect repository: {e}")
            
        logger.info("❌ Could not auto-detect repository")
        return None

    def handle_claude_request(self, user_input: str) -> str:
        """Handle a request from Claude CLI"""
        logger.info("📝 Handling Claude CLI request...")
        logger.debug(f"📝 User input: {user_input}")
        
        # Check if this is a PR review request
        pr_keywords = ['review', 'analyze', 'check', 'examine', 'pr', 'pull request']
        
        if not any(keyword in user_input.lower() for keyword in pr_keywords):
            response = "This doesn't appear to be a PR review request. Try: 'review PR 123'"
            logger.info(f"❌ Not a PR review request: {response}")
            return response
        
        # Parse the command
        command = self.parse_natural_language_command(user_input)
        
        if not command["pr_number"]:
            response = """❌ I couldn't find a PR number in your request. 

Try these formats:
- "review PR 123"
- "analyze pull request #456" 
- "check PR number 789"
"""
            logger.info("❌ No PR number found in request")
            return response
        
        # Execute the review
        success = self.execute_review(command)
        
        if success:
            response = f"✅ PR review completed for #{command['pr_number']}"
            logger.info("✅ Claude request handled successfully")
        else:
            response = "❌ PR review failed. Check the logs above for details."
            logger.error("❌ Claude request failed")
            
        return response 