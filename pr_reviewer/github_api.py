"""
GitHub API wrapper for PR operations.
"""

import os
import time
import logging
from typing import Dict, List, Optional

import requests
from github import Github

from .models import ReviewComment

logger = logging.getLogger(__name__)

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
        
        #token_vars = ["GITHUB_TOKEN_WORK", "GITHUB_TOKEN", "GITHUB_TOKEN_PERSONAL"]
        token_vars = ["GITHUB_TOKEN_PERSONAL"]
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
    
    def extract_code_context(self, patch: str, target_line: int) -> dict:
        """Extract original code context from a patch for generating suggestions"""
        logger.debug(f"🔍 Extracting code context for line {target_line} from patch")
        
        if not patch:
            return {"original_lines": [], "line_numbers": [], "context_start": 0}
        
        lines = patch.split('\n')
        context = {
            "original_lines": [],
            "line_numbers": [],
            "context_start": 0,
            "hunk_info": None
        }
        
        current_line_new = 0
        current_line_old = 0
        in_target_hunk = False
        
        for line in lines:
            # Parse hunk headers (@@)
            if line.startswith('@@'):
                # Extract line numbers from hunk header: @@ -old_start,old_count +new_start,new_count @@
                import re
                match = re.match(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
                if match:
                    current_line_old = int(match.group(1))
                    current_line_new = int(match.group(2))
                    context["hunk_info"] = line
                    
                    # Check if our target line is in this hunk
                    # We need to look ahead to see if target_line falls in this range
                    continue
            
            # Skip diff metadata
            if line.startswith('diff ') or line.startswith('index ') or line.startswith('---') or line.startswith('+++'):
                continue
            
            # Process actual diff content
            if line.startswith('-'):
                # Removed line (only in old version)
                if current_line_old <= target_line <= current_line_old + 3:  # Context window
                    context["original_lines"].append(line[1:])  # Remove the '-' prefix
                    context["line_numbers"].append(current_line_old)
                    in_target_hunk = True
                current_line_old += 1
            elif line.startswith('+'):
                # Added line (only in new version)
                if current_line_new <= target_line <= current_line_new + 3:  # Context window
                    in_target_hunk = True
                current_line_new += 1
            else:
                # Context line (in both versions)
                if (current_line_new <= target_line <= current_line_new + 3 or 
                    current_line_old <= target_line <= current_line_old + 3):
                    context["original_lines"].append(line[1:] if line.startswith(' ') else line)
                    context["line_numbers"].append(current_line_new)
                    in_target_hunk = True
                current_line_old += 1
                current_line_new += 1
        
        if context["line_numbers"]:
            context["context_start"] = min(context["line_numbers"])
        
        logger.debug(f"✅ Extracted {len(context['original_lines'])} lines of context")
        return context
    
    def validate_suggestion(self, comment: ReviewComment, patch: str) -> bool:
        """Validate if a suggestion can be properly applied to the code"""
        if not comment.has_suggestion():
            return True  # Non-suggestion comments are always valid
        
        logger.debug(f"🔍 Validating suggestion for {comment.file_path}:{comment.line_number}")
        
        # Extract context around the target line
        context = self.extract_code_context(patch, comment.line_number)
        
        if not context["original_lines"]:
            logger.warning(f"⚠️ No code context found for line {comment.line_number}")
            return False
        
        # Check if the original code in the suggestion matches the actual code
        original_code_lines = comment.original_code.split('\n') if comment.original_code else []
        
        # Simple validation: check if any of the original code lines appear in the context
        context_text = '\n'.join(context["original_lines"]).lower()
        
        for orig_line in original_code_lines:
            if orig_line.strip().lower() in context_text:
                logger.debug("✅ Suggestion validation passed")
                return True
        
        logger.warning(f"⚠️ Original code in suggestion doesn't match context for {comment.file_path}:{comment.line_number}")
        return False
    
    def post_review_comments(self, repo_name: str, pr_number: int, 
                           comments: List[ReviewComment], dry_run: bool = True) -> bool:
        """Post review comments to PR with GitHub suggestion support"""
        logger.info(f"💬 {'DRY RUN: Would post' if dry_run else 'Posting'} {len(comments)} comments to PR #{pr_number}")
        
        # Count suggestions for logging
        suggestions_count = sum(1 for comment in comments if comment.has_suggestion())
        if suggestions_count > 0:
            logger.info(f"✨ {suggestions_count} comments include code suggestions")
        
        if dry_run:
            print("\n🔍 DRY RUN - Comments that would be posted:")
            for i, comment in enumerate(comments, 1):
                print(f"\n📝 Comment {i} ({comment.severity}):")
                print(f"   File: {comment.file_path}:{comment.line_number}")
                if comment.has_suggestion():
                    print(f"   ✨ Includes suggestion: {comment.suggestion_type}")
                    print(f"   📄 Suggestion preview: {comment.suggested_code[:50]}...")
                print(f"   Body: {comment.format_with_suggestion()[:200]}...")
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
            suggestions_posted = 0
            for i, comment in enumerate(comments, 1):
                try:
                    logger.debug(f"📝 Posting comment {i}/{len(comments)}: {comment.file_path}:{comment.line_number}")
                    
                    # Use the enhanced formatting that includes suggestions
                    formatted_body = comment.format_with_suggestion()
                    
                    # For multi-line suggestions, we need to specify the line range
                    if comment.suggestion_type == "multi_line" and comment.end_line_number:
                        # GitHub API supports line ranges for multi-line comments
                        pr.create_review_comment(
                            body=formatted_body,
                            commit=pr.get_commits().reversed[0],  # Latest commit
                            path=comment.file_path,
                            line=comment.end_line_number,  # End line for multi-line
                            start_line=comment.line_number,  # Start line for multi-line
                            start_side="RIGHT",  # Comment on the new version
                            side="RIGHT"
                        )
                    else:
                        # Single line comment (traditional approach)
                        pr.create_review_comment(
                            body=formatted_body,
                            commit=pr.get_commits().reversed[0],  # Latest commit
                            path=comment.file_path,
                            line=comment.line_number
                        )
                    
                    posted_count += 1
                    if comment.has_suggestion():
                        suggestions_posted += 1
                    logger.debug(f"✅ Posted comment {i} successfully")
                    
                    # Add delay between comments to avoid rate limiting
                    if i < len(comments):
                        time.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to post comment {i} to {comment.file_path}:{comment.line_number}: {e}")
                    # Continue with other comments even if one fails
                    continue
            
            logger.info(f"✅ Successfully posted {posted_count}/{len(comments)} review comments to PR #{pr_number}")
            if suggestions_posted > 0:
                logger.info(f"✨ Posted {suggestions_posted} comments with code suggestions")
            print(f"✅ Posted {posted_count}/{len(comments)} review comments to PR #{pr_number}")
            if suggestions_posted > 0:
                print(f"✨ {suggestions_posted} comments include code suggestions that can be applied directly!")
            
            # Also create a general review summary if we have comments
            if posted_count > 0:
                try:
                    summary_parts = [
                        "🤖 **AI Code Review Summary**",
                        f"Posted {posted_count} detailed comments on this PR."
                    ]
                    
                    if suggestions_posted > 0:
                        summary_parts.append(f"✨ {suggestions_posted} comments include code suggestions that you can apply directly by clicking the **'Apply suggestion'** button.")
                    
                    summary_parts.append("Please review the suggestions and let me know if you have any questions!")
                    
                    summary_body = "\n\n".join(summary_parts)
                    pr.create_review(body=summary_body, event="COMMENT")
                    logger.info("✅ Posted review summary")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to post review summary: {e}")
            
            return posted_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to post comments: {e}")
            return False 