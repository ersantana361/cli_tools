#!/usr/bin/env python3
"""
Example script demonstrating how to use the enhanced PR reviewer with GitHub suggestion blocks.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from pr_reviewer import ClaudeIntegratedPRReviewer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Demonstrate PR review with GitHub suggestions"""
    print("🚀 GitHub Suggestion Blocks Demo")
    print("=" * 50)
    
    # Initialize the PR reviewer
    try:
        reviewer = ClaudeIntegratedPRReviewer()
    except Exception as e:
        print(f"❌ Failed to initialize PR reviewer: {e}")
        print("\n💡 Make sure you have:")
        print("   - GITHUB_TOKEN_PERSONAL environment variable set")
        print("   - ANTHROPIC_API_KEY environment variable set")
        return 1
    
    # Example usage scenarios
    print("\n📋 Example Commands with Suggestion Support:")
    print("-" * 50)
    
    examples = [
        "review PR 123 in owner/repo with suggestions",
        "security review PR 456 in myorg/myproject with fixes",
        "performance review PR 789 in company/codebase with optimizations",
        "maintainability review PR 101 in team/service with refactoring"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    
    print("\n✨ New Features:")
    print("-" * 20)
    print("• 🔧 GitHub suggestion blocks for direct code fixes")
    print("• 📝 Single-line and multi-line suggestions")
    print("• 🎯 Actionable code improvements you can apply with one click")
    print("• 📊 Enhanced reporting showing suggestion counts")
    print("• 🔍 Smart code context extraction from diffs")
    
    print("\n📖 How GitHub Suggestions Work:")
    print("-" * 35)
    print("1. AI analyzes your PR and identifies improvable code")
    print("2. For each issue, it extracts the original code")
    print("3. It generates improved/corrected code")
    print("4. Comments are posted with ```suggestion blocks")
    print("5. You click 'Apply suggestion' to accept changes")
    
    print("\n🛠️  Example Suggestion Types:")
    print("-" * 30)
    suggestion_types = [
        "🔒 Security fixes (SQL injection, XSS prevention)",
        "⚡ Performance optimizations (algorithm improvements)",
        "🧹 Code cleanup (naming, structure, readability)",
        "🐛 Bug fixes (logic errors, edge cases)",
        "📚 Best practices (error handling, validation)"
    ]
    
    for suggestion_type in suggestion_types:
        print(f"   {suggestion_type}")
    
    print("\n🎮 Try it out:")
    print("-" * 15)
    print("1. Run the reviewer with any PR")
    print("2. Look for ✨ indicators in the output")
    print("3. Check the PR for suggestion blocks")
    print("4. Apply suggestions directly in GitHub!")
    
    print("\n🎯 Pro Tips:")
    print("-" * 12)
    print("• Use 'security review' for vulnerability fixes")
    print("• Use 'performance review' for optimization suggestions") 
    print("• Use 'maintainability review' for code cleanup")
    print("• Regular review combines all suggestion types")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 