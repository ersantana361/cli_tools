#!/usr/bin/env python3
"""
claude_integrated_pr_review.py - Enhanced version that can be called by Claude CLI

This script can be executed directly by Claude CLI when you ask it to review PRs.
"""

import sys
import re
import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# GitHub and AI imports
try:
    print("🔄 Importing dependencies...")
    from github import Github
    import requests
    print("✅ GitHub imports successful")
    
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    print("✅ LangChain imports successful")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("📦 Install missing dependencies with: pip install PyGithub langchain-openai langchain-anthropic requests")
    logger.error(f"Import failed: {e}")

@dataclass
class ReviewComment:
    """Represents a review comment"""
    file_path: str
    line_number: int
    body: str
    severity: str = "info"  # info, warning, error

@dataclass 
class PRReviewResult:
    """Represents the result of a PR review"""
    pr_number: int
    summary: str
    comments: List[ReviewComment]
    overall_score: str
    recommendations: List[str]

class GitHubAPI:
    """GitHub API wrapper for PR operations"""
    
    def __init__(self):
        logger.info("🔧 Initializing GitHub API client...")
        self.token = self._get_token()
        
        if self.token:
            logger.info(f"✅ GitHub token found (ends with: ...{self.token[-4:]})")
            try:
                self.github = Github(self.token)
                # Test the connection
                user = self.github.get_user()
                logger.info(f"✅ GitHub API connection successful. Authenticated as: {user.login}")
            except Exception as e:
                logger.error(f"❌ GitHub API connection failed: {e}")
                self.github = None
        else:
            logger.error("❌ No GitHub token found in environment variables")
            self.github = None
    
    def _get_token(self) -> Optional[str]:
        """Get GitHub token from environment"""
        logger.debug("🔍 Looking for GitHub token in environment variables...")
        
        token_vars = ["GITHUB_TOKEN_WORK", "GITHUB_TOKEN", "GITHUB_TOKEN_PERSONAL"]
        for var in token_vars:
            token = os.getenv(var)
            if token:
                logger.info(f"✅ Found GitHub token in {var}")
                return token
            else:
                logger.debug(f"❌ {var} not set")
        
        logger.error("❌ No GitHub token found in any of: " + ", ".join(token_vars))
        return None
    
    def get_pr_info(self, repo_name: str, pr_number: int) -> dict:
        """Get PR information"""
        logger.info(f"📥 Fetching PR #{pr_number} info from {repo_name}...")
        
        if not self.github:
            error_msg = "GitHub API client not initialized"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        try:
            logger.debug(f"🔍 Getting repository: {repo_name}")
            repo = self.github.get_repo(repo_name)
            logger.debug(f"✅ Repository found: {repo.full_name}")
            
            logger.debug(f"🔍 Getting PR #{pr_number}")
            pr = repo.get_pull(pr_number)
            logger.debug(f"✅ PR found: {pr.title}")
            
            pr_info = {
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "author": pr.user.login,
                "url": pr.html_url,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "files_changed": pr.changed_files,
                "additions": pr.additions,
                "deletions": pr.deletions
            }
            
            logger.info(f"✅ PR info retrieved successfully:")
            logger.info(f"   📋 Title: {pr_info['title']}")
            logger.info(f"   👤 Author: {pr_info['author']}")
            logger.info(f"   📊 State: {pr_info['state']}")
            logger.info(f"   📁 Files changed: {pr_info['files_changed']}")
            logger.info(f"   ➕ Additions: {pr_info['additions']}")
            logger.info(f"   ➖ Deletions: {pr_info['deletions']}")
            
            return pr_info
            
        except Exception as e:
            logger.error(f"❌ Failed to get PR info: {e}")
            logger.error(f"   Repository: {repo_name}")
            logger.error(f"   PR Number: {pr_number}")
            raise Exception(f"Failed to fetch PR info: {str(e)}")
    
    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """Get PR diff"""
        logger.info(f"📄 Fetching diff for PR #{pr_number} from {repo_name}...")
        
        if not self.github:
            error_msg = "GitHub API client not initialized"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            logger.debug(f"🔍 Making API request for diff...")
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3.diff"
            }
            
            logger.debug(f"📡 Request URL: {pr.url}")
            response = requests.get(pr.url, headers=headers)
            
            logger.debug(f"📡 Response status: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"Failed to fetch diff: HTTP {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            diff_text = response.text
            logger.info(f"✅ Diff retrieved successfully ({len(diff_text)} characters)")
            logger.debug(f"📄 Diff preview (first 200 chars): {diff_text[:200]}...")
            
            return diff_text
            
        except Exception as e:
            logger.error(f"❌ Failed to get PR diff: {e}")
            raise Exception(f"Failed to fetch PR diff: {str(e)}")
    
    def get_pr_files(self, repo_name: str, pr_number: int) -> List[dict]:
        """Get list of files changed in PR"""
        logger.info(f"📁 Fetching file list for PR #{pr_number} from {repo_name}...")
        
        if not self.github:
            error_msg = "GitHub API client not initialized"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            files = []
            file_count = 0
            for file in pr.get_files():
                file_count += 1
                file_info = {
                    "filename": file.filename,
                    "status": file.status,  # added, removed, modified
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch or ""
                }
                files.append(file_info)
                logger.debug(f"📄 File {file_count}: {file.filename} ({file.status})")
            
            logger.info(f"✅ Retrieved {len(files)} changed files")
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to get PR files: {e}")
            raise Exception(f"Failed to fetch PR files: {str(e)}")
    
    def post_review_comments(self, repo_name: str, pr_number: int, 
                           comments: List[ReviewComment], dry_run: bool = True) -> bool:
        """Post review comments to PR"""
        logger.info(f"💬 {'DRY RUN: Would post' if dry_run else 'Posting'} {len(comments)} comments to PR #{pr_number}")
        
        if dry_run:
            print("\n🔍 DRY RUN - Comments that would be posted:")
            for i, comment in enumerate(comments, 1):
                print(f"\n📝 Comment {i} ({comment.severity}):")
                print(f"   File: {comment.file_path}:{comment.line_number}")
                print(f"   Body: {comment.body}")
                logger.debug(f"DRY RUN Comment {i}: {comment.file_path}:{comment.line_number}")
            return True
        
        if not self.github:
            error_msg = "GitHub API client not initialized"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        try:
            logger.info("🚀 Starting to post review comments to GitHub...")
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get the latest commit SHA for the review
            commit_sha = pr.head.sha
            logger.debug(f"📝 Using commit SHA: {commit_sha}")
            
            # Post individual review comments
            posted_count = 0
            for i, comment in enumerate(comments, 1):
                try:
                    logger.debug(f"📝 Posting comment {i}/{len(comments)}: {comment.file_path}:{comment.line_number}")
                    
                    # GitHub API call to create review comment
                    pr.create_review_comment(
                        body=comment.body,
                        commit=pr.get_commits().reversed[0],  # Latest commit
                        path=comment.file_path,
                        line=comment.line_number
                    )
                    posted_count += 1
                    logger.debug(f"✅ Posted comment {i} successfully")
                    
                    # Add delay between comments to avoid rate limiting
                    if i < len(comments):
                        time.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to post comment {i} to {comment.file_path}:{comment.line_number}: {e}")
                    # Continue with other comments even if one fails
                    continue
            
            logger.info(f"✅ Successfully posted {posted_count}/{len(comments)} review comments to PR #{pr_number}")
            print(f"✅ Posted {posted_count}/{len(comments)} review comments to PR #{pr_number}")
            
            # Also create a general review summary if we have comments
            if posted_count > 0:
                try:
                    summary_body = f"🤖 **AI Code Review Summary**\n\nPosted {posted_count} detailed comments on this PR. Please review the suggestions and let me know if you have any questions!"
                    pr.create_review(body=summary_body, event="COMMENT")
                    logger.info("✅ Posted review summary")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to post review summary: {e}")
            
            return posted_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to post comments: {e}")
            return False

class LLMAnalyzer:
    """LLM-based code analysis"""
    
    def __init__(self, provider: str = "anthropic"):
        logger.info(f"🧠 Initializing LLM analyzer with provider: {provider}")
        self.provider = provider
        try:
            self.llm = self._initialize_llm()
            logger.info(f"✅ LLM initialized successfully")
        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            raise
    
    def _initialize_llm(self):
        """Initialize LLM based on provider"""
        logger.debug(f"🔧 Setting up {self.provider} LLM...")
        
        if self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                error_msg = "ANTHROPIC_API_KEY environment variable not set"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            logger.debug(f"✅ Anthropic API key found (ends with: ...{api_key[-4:]})")
            
            try:
                llm = ChatAnthropic(
                    api_key=api_key,
                    model="claude-opus-4-20250514"
                )
                logger.info("✅ Claude LLM initialized")
                return llm
            except Exception as e:
                logger.error(f"❌ Failed to initialize Claude: {e}")
                raise
                
        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                error_msg = "OPENAI_API_KEY environment variable not set"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            logger.debug(f"✅ OpenAI API key found (ends with: ...{api_key[-4:]})")
            
            try:
                llm = ChatOpenAI(
                    api_key=api_key,
                    model="gpt-4o"
                )
                logger.info("✅ GPT LLM initialized")
                return llm
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
                raise
        else:
            error_msg = f"Unsupported LLM provider: {self.provider}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def analyze_pr_diff(self, diff: str, pr_info: dict, review_type: str) -> str:
        """Analyze PR diff with LLM"""
        logger.info(f"🤖 Starting AI analysis...")
        logger.info(f"   📋 Review type: {review_type}")
        logger.info(f"   📄 Diff length: {len(diff)} characters")
        logger.info(f"   🏷️  PR title: {pr_info.get('title', 'N/A')}")
        
        try:
            prompt = self._build_analysis_prompt(diff, pr_info, review_type)
            logger.debug(f"📝 Generated prompt ({len(prompt)} characters)")
            logger.debug(f"📝 Prompt preview: {prompt[:300]}...")
            
            logger.info("🚀 Sending request to LLM...")
            response = self.llm.invoke(prompt)
            
            analysis = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"✅ LLM analysis completed ({len(analysis)} characters)")
            logger.debug(f"📄 Analysis preview: {analysis[:200]}...")
            
            return analysis
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"   Provider: {self.provider}")
            logger.error(f"   Review type: {review_type}")
            return error_msg
    
    def generate_actionable_comments(self, diff: str, pr_info: dict, files: List[dict], review_type: str) -> List[ReviewComment]:
        """Generate actionable review comments by analyzing individual files"""
        logger.info("🔨 Generating actionable review comments...")
        
        comments = []
        
        try:
            # Build a more targeted prompt for generating specific comments
            prompt = self._build_comment_generation_prompt(diff, pr_info, files, review_type)
            logger.debug(f"📝 Generated comment prompt ({len(prompt)} characters)")
            
            logger.info("🚀 Sending comment generation request to LLM...")
            response = self.llm.invoke(prompt)
            
            analysis = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"✅ Comment analysis completed ({len(analysis)} characters)")
            
            # Parse the analysis to extract actionable comments
            comments = self._parse_analysis_to_comments(analysis, files)
            logger.info(f"✅ Generated {len(comments)} actionable comments")
            
            return comments
            
        except Exception as e:
            logger.error(f"❌ Failed to generate actionable comments: {e}")
            return []
    
    def _build_comment_generation_prompt(self, diff: str, pr_info: dict, files: List[dict], review_type: str) -> str:
        """Build prompt specifically for generating actionable comments"""
        logger.debug(f"🔨 Building comment generation prompt for {review_type}...")
        
        files_summary = "\n".join([f"- {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})" for f in files[:10]])
        
        base_prompt = f"""
You are an expert code reviewer. Analyze this pull request and generate specific, actionable review comments.

**PR Info:**
- Title: {pr_info.get('title', 'N/A')}
- Author: {pr_info.get('author', 'N/A')}
- Files changed: {pr_info.get('files_changed', 0)}

**Changed Files:**
{files_summary}

**Full Diff:**
```
{diff}
```

Please provide specific review comments in this EXACT format:
FILE: filename.ext
LINE: 42
SEVERITY: warning|error|info
COMMENT: Your specific actionable feedback here

"""
        
        if review_type == "security":
            prompt = base_prompt + """
Focus on security issues:
- Look for SQL injection, XSS, authentication bypasses
- Check for hardcoded secrets, unsafe input handling
- Flag authorization issues and data validation problems
- Identify potential security vulnerabilities

Provide 2-5 specific security-focused comments with exact file names and line numbers.
"""
        elif review_type == "performance":
            prompt = base_prompt + """
Focus on performance issues:
- Identify inefficient algorithms, database queries, loops
- Look for memory leaks, resource management issues
- Check for unnecessary computations, network calls
- Suggest optimization opportunities

Provide 2-5 specific performance-focused comments with exact file names and line numbers.
"""
        elif review_type == "maintainability":
            prompt = base_prompt + """
Focus on code maintainability:
- Check code organization, structure, naming conventions
- Look for code duplication, complex functions
- Assess documentation, error handling
- Identify refactoring opportunities

Provide 2-5 specific maintainability-focused comments with exact file names and line numbers.
"""
        else:  # categorized or other
            prompt = base_prompt + """
Provide a comprehensive review covering:
1. **Security** - Any security concerns or vulnerabilities
2. **Performance** - Potential performance issues
3. **Code Quality** - Maintainability, readability, best practices
4. **Logic** - Correctness of implementation
5. **Testing** - Missing tests or test improvements

Provide 3-8 specific comments covering different aspects, with exact file names and line numbers.
"""
        
        return prompt + "\n\nIMPORTANT: Only comment on files that actually exist in the diff. Use the EXACT format shown above."
    
    def _parse_analysis_to_comments(self, analysis: str, files: List[dict]) -> List[ReviewComment]:
        """Parse LLM analysis into structured review comments"""
        logger.debug("🔍 Parsing analysis into structured comments...")
        
        comments = []
        file_names = [f['filename'] for f in files]
        
        # Split analysis into sections and look for the structured format
        lines = analysis.split('\n')
        current_comment = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('FILE:'):
                if current_comment:
                    # Save previous comment if complete
                    if all(k in current_comment for k in ['file', 'line', 'comment']):
                        comments.append(ReviewComment(
                            file_path=current_comment['file'],
                            line_number=current_comment['line'],
                            body=current_comment['comment'],
                            severity=current_comment.get('severity', 'info')
                        ))
                
                # Start new comment
                filename = line.replace('FILE:', '').strip()
                # Validate file exists in the PR
                if filename in file_names:
                    current_comment = {'file': filename}
                else:
                    current_comment = {}  # Skip invalid files
                    
            elif line.startswith('LINE:') and current_comment:
                try:
                    line_num = int(line.replace('LINE:', '').strip())
                    current_comment['line'] = line_num
                except ValueError:
                    current_comment['line'] = 1  # Default to line 1 if parsing fails
                    
            elif line.startswith('SEVERITY:') and current_comment:
                severity = line.replace('SEVERITY:', '').strip().lower()
                if severity in ['warning', 'error', 'info']:
                    current_comment['severity'] = severity
                    
            elif line.startswith('COMMENT:') and current_comment:
                comment_text = line.replace('COMMENT:', '').strip()
                current_comment['comment'] = comment_text
        
        # Don't forget the last comment
        if current_comment and all(k in current_comment for k in ['file', 'line', 'comment']):
            comments.append(ReviewComment(
                file_path=current_comment['file'],
                line_number=current_comment['line'],
                body=current_comment['comment'],
                severity=current_comment.get('severity', 'info')
            ))
        
        # If structured parsing didn't work well, fall back to extracting insights
        if len(comments) < 2:
            logger.warning("⚠️ Structured parsing yielded few comments, using fallback method...")
            comments.extend(self._extract_fallback_comments(analysis, files[:5]))
        
        logger.info(f"✅ Parsed {len(comments)} comments from analysis")
        return comments[:8]  # Limit to 8 comments max
    
    def _extract_fallback_comments(self, analysis: str, files: List[dict]) -> List[ReviewComment]:
        """Fallback method to extract comments when structured parsing fails"""
        logger.debug("🔄 Using fallback comment extraction...")
        
        comments = []
        sentences = re.split(r'[.!?]+', analysis)
        
        # Look for actionable sentences and map them to files
        for sentence in sentences[:10]:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
                
            # Check if sentence mentions any file
            mentioned_file = None
            for file_info in files:
                if file_info['filename'] in sentence or file_info['filename'].split('.')[-1] in sentence:
                    mentioned_file = file_info
                    break
            
            # Create comments for files with actionable feedback
            if mentioned_file and any(keyword in sentence.lower() for keyword in [
                'should', 'could', 'consider', 'recommend', 'suggest', 'improve', 
                'issue', 'problem', 'vulnerability', 'performance', 'optimize'
            ]):
                comments.append(ReviewComment(
                    file_path=mentioned_file['filename'],
                    line_number=1,  # Default to line 1 for fallback
                    body=f"📝 **Review Suggestion:**\n\n{sentence.strip()}\n\n*This comment was generated from AI analysis.*",
                    severity="info"
                ))
        
        # If still no good comments, create at least one summary comment for the main file
        if not comments and files:
            main_file = files[0]  # Use the first file
            comments.append(ReviewComment(
                file_path=main_file['filename'],
                line_number=1,
                body=f"📋 **AI Review Summary:**\n\n{analysis[:500]}...\n\n*Please review the changes for potential improvements.*",
                severity="info"
            ))
        
        return comments
    
    def _build_analysis_prompt(self, diff: str, pr_info: dict, review_type: str) -> str:
        """Build analysis prompt based on review type"""
        logger.debug(f"🔨 Building {review_type} analysis prompt...")
        
        base_prompt = f"""
You are an expert code reviewer. Analyze this pull request:

**PR Info:**
- Title: {pr_info.get('title', 'N/A')}
- Author: {pr_info.get('author', 'N/A')}
- Files changed: {pr_info.get('files_changed', 0)}
- Additions: +{pr_info.get('additions', 0)} lines
- Deletions: -{pr_info.get('deletions', 0)} lines

**Diff:**
```
{diff}
```

"""
        
        if review_type == "security":
            prompt = base_prompt + """
Focus on security vulnerabilities:
- Look for SQL injection, XSS, authentication issues
- Check for hardcoded secrets or credentials
- Identify unsafe input handling
- Flag potential authorization bypasses
"""
            logger.debug("✅ Built security-focused prompt")
        elif review_type == "performance":
            prompt = base_prompt + """
Focus on performance issues:
- Identify inefficient algorithms or database queries
- Look for memory leaks or resource management issues
- Check for unnecessary computations or network calls
- Suggest optimization opportunities
"""
            logger.debug("✅ Built performance-focused prompt")
        elif review_type == "maintainability":
            prompt = base_prompt + """
Focus on code maintainability:
- Check code organization and structure
- Look for code duplication
- Assess naming conventions and documentation
- Identify areas that need refactoring
"""
            logger.debug("✅ Built maintainability-focused prompt")
        else:  # categorized (default)
            prompt = base_prompt + """
Provide a comprehensive review covering:
1. **Security** - Any security concerns or vulnerabilities
2. **Performance** - Potential performance issues or improvements
3. **Code Quality** - Maintainability, readability, best practices
4. **Logic** - Correctness of the implementation
5. **Testing** - Are there adequate tests for the changes?

Format as sections with specific examples from the code.
"""
            logger.debug("✅ Built categorized (comprehensive) prompt")
        
        return prompt + "\nProvide actionable feedback with specific line references where possible."

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
            import subprocess
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
    
    def _generate_file_comments(self, repo_name: str, pr_number: int, analysis: str) -> List[ReviewComment]:
        """Generate specific file comments from analysis - DEPRECATED, use LLMAnalyzer.generate_actionable_comments instead"""
        logger.warning("⚠️ Using deprecated _generate_file_comments method")
        
        comments = []
        
        try:
            files = self.github_api.get_pr_files(repo_name, pr_number)
            logger.info(f"📁 Processing {len(files)} changed files")
            
            # Simple fallback: create one comment per changed file
            for i, file_info in enumerate(files[:3]):  # Limit to first 3 files
                if file_info['status'] in ['added', 'modified']:
                    logger.debug(f"💬 Creating fallback comment for {file_info['filename']}")
                    
                    comment = ReviewComment(
                        file_path=file_info['filename'],
                        line_number=1,
                        body=f"📋 **Analysis for {file_info['filename']}:**\n\n{analysis[:300]}...\n\n*Please review the AI analysis above for detailed feedback.*",
                        severity="info"
                    )
                    comments.append(comment)
                    
            logger.info(f"✅ Generated {len(comments)} fallback file comments")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not generate file comments: {e}")
        
        return comments

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
