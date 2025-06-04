"""
Data models for PR review system.
"""

from dataclasses import dataclass
from typing import List

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