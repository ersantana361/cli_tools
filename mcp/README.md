# Claude Integrated PR Review Tool

A sophisticated PR review tool that can be called directly by Claude CLI to analyze GitHub pull requests with AI-powered insights.

## Features

🤖 **AI-Powered Analysis** - Uses Claude or GPT models to provide comprehensive code reviews
🔍 **Security Focused** - Identifies potential vulnerabilities and security issues  
⚡ **Performance Review** - Spots performance bottlenecks and optimization opportunities
🧹 **Code Quality** - Checks maintainability, readability, and best practices
📝 **Smart Comments** - Can post targeted comments to specific files and lines
🔄 **Dry Run Mode** - Test reviews without posting comments
🎯 **Flexible Types** - Supports different review focuses (security, performance, etc.)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Set up your API keys:

```bash
# GitHub access (required)
export GITHUB_TOKEN_WORK="your_github_token"
# OR
export GITHUB_TOKEN="your_github_token"

# AI Provider (choose one)
export ANTHROPIC_API_KEY="your_anthropic_key"
# OR  
export OPENAI_API_KEY="your_openai_key"
```

### 3. Configuration (Optional)
Copy the example config and customize:
```bash
cp .claude_pr_config.json.example .claude_pr_config.json
```

## Usage

### Basic Usage
```bash
# Review a PR (dry run by default)
python claude_integrated_pr_review.py "review PR 123 in owner/repo"

# Security-focused review
python claude_integrated_pr_review.py "security review PR 456 in owner/repo"

# Performance analysis
python claude_integrated_pr_review.py "performance review PR 789 in owner/repo"
```

### Review Types

- **`categorized`** (default) - Comprehensive review covering security, performance, code quality
- **`security`** - Focus on vulnerabilities, auth issues, input validation
- **`performance`** - Identify bottlenecks, inefficient queries, optimization opportunities  
- **`maintainability`** - Code organization, duplication, refactoring suggestions
- **`files`** - Review each changed file separately with targeted comments
- **`summary`** - High-level overview only
- **`all`** - Comprehensive analysis with file-by-file comments

### Advanced Usage

```bash
# Actually post comments (not dry run)
python claude_integrated_pr_review.py "actually post security review for PR 123 in owner/repo"

# If you're in a git repo, you can omit the repo name
python claude_integrated_pr_review.py "review PR 123"

# Various natural language formats work
python claude_integrated_pr_review.py "analyze pull request #456 for performance issues"
python claude_integrated_pr_review.py "check PR number 789 for security vulnerabilities"
```

## Claude CLI Integration

This tool is designed to work seamlessly with Claude CLI. You can ask Claude:

- "Review PR 123 in my-org/my-repo"
- "Do a security analysis of pull request 456"  
- "Check PR #789 for performance issues"
- "Actually post the review comments for PR 123"

## MCP Server

The tool also includes an MCP server for integration with Claude Desktop:

```bash
python pr_review_mcp_server.py
```

Register it in your Claude Desktop settings to use the `review_github_pr` tool.

## Configuration Options

```json
{
  "max_comments": 8,           // Max comments to post per review
  "comment_delay": 2,          // Delay between posting comments (seconds)
  "default_review_type": "categorized",  // Default analysis type
  "auto_dry_run": true,        // Always dry run first
  "confirmation_required": true,         // Require confirmation for posts
  "llm_provider": "anthropic", // "anthropic" or "openai"
  "default_repo": "owner/repo" // Default repo if not specified
}
```

## How It Works

1. **Fetch PR Data** - Uses GitHub API to get PR info, diff, and file changes
2. **AI Analysis** - Sends code changes to Claude/GPT with specialized prompts
3. **Generate Report** - Creates comprehensive analysis with actionable feedback
4. **Optional Comments** - Can post targeted comments to specific files/lines
5. **Safety First** - Dry run mode prevents accidental comment posting

## Examples

### Security Review
```bash
python claude_integrated_pr_review.py "security review PR 123 in myorg/myapp"
```

Output includes:
- SQL injection vulnerability checks
- Authentication/authorization issues  
- Hardcoded secrets detection
- Input validation problems
- XSS vulnerability analysis

### Performance Review  
```bash
python claude_integrated_pr_review.py "performance review PR 456 in myorg/myapp"
```

Output includes:
- Database query optimization
- Algorithm efficiency analysis
- Memory usage patterns
- Network call optimization
- Resource management issues

## Troubleshooting

### GitHub Token Issues
- Ensure your token has `repo` scope for private repositories
- Use `GITHUB_TOKEN_WORK` for work repositories, `GITHUB_TOKEN` for personal

### LLM Provider Issues
- Check that your API key is correctly set
- Verify the provider name in config ("anthropic" or "openai")
- Ensure you have sufficient API credits

### Repository Detection
- If auto-detection fails, explicitly specify: `owner/repo`
- Ensure you're in a git repository for auto-detection
- Check that remote origin points to GitHub

## Contributing

Feel free to submit issues and enhancement requests! Key areas for improvement:
- More sophisticated comment placement logic
- Additional review types (accessibility, testing, etc.)
- Better parsing of AI analysis for targeted comments
- Integration with more LLM providers 