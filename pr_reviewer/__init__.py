"""
PR Reviewer Package - Enhanced version that can be called by Claude CLI

This package provides modular components for automated PR review using AI.
"""

from .models import ReviewComment, PRReviewResult
from .github_api import GitHubAPI
from .llm_analyzer import LLMAnalyzer
from .reviewer import ClaudeIntegratedPRReviewer

__version__ = "1.0.0"
__author__ = "Claude AI Assistant"

__all__ = [
    "ReviewComment",
    "PRReviewResult", 
    "GitHubAPI",
    "LLMAnalyzer",
    "ClaudeIntegratedPRReviewer"
] 