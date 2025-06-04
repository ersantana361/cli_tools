"""
Data models for PR review system.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ReviewComment:
    """Represents a review comment"""
    file_path: str
    line_number: int
    body: str
    severity: str = "info"  # info, warning, error
    # New fields for GitHub suggestions
    suggestion_type: Optional[str] = None  # "single_line", "multi_line", None
    original_code: Optional[str] = None  # Original code to be replaced
    suggested_code: Optional[str] = None  # Suggested replacement code
    end_line_number: Optional[int] = None  # For multi-line suggestions

    def has_suggestion(self) -> bool:
        """Check if this comment includes a code suggestion"""
        return self.suggestion_type is not None and self.suggested_code is not None

    def format_with_suggestion(self) -> str:
        """Format the comment body with GitHub suggestion block"""
        if not self.has_suggestion():
            return self.body
        
        # Build the suggestion block
        suggestion_block = f"```suggestion\n{self.suggested_code}\n```"
        
        # Combine comment body with suggestion
        if self.body.strip():
            return f"{self.body}\n\n{suggestion_block}"
        else:
            return suggestion_block

@dataclass 
class PRReviewResult:
    """Represents the result of a PR review"""
    pr_number: int
    summary: str
    comments: List[ReviewComment]
    overall_score: str
    recommendations: List[str]
    suggestions_count: int = 0  # Track how many comments have suggestions

    def __post_init__(self):
        """Calculate suggestions count after initialization"""
        self.suggestions_count = sum(1 for comment in self.comments if comment.has_suggestion()) 