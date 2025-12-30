# PR Review Guide

[Home](../README.md) > [Guides](README.md) > PR Review

Guide to analyzing GitHub pull requests with AI.

## Overview

The PR review tool analyzes GitHub pull requests to provide:
- Code quality assessment
- Security review
- Performance considerations
- Actionable recommendations

## Basic Workflow

### 1. Analyze a PR

```bash
ai github "https://github.com/owner/repo/pull/123"
```

### 2. Review the Output

The analysis includes:
- **Summary** - What the PR does
- **Code Review** - Quality and security findings
- **Recommendations** - Suggested improvements

## Understanding the Analysis

### Summary Section

Provides an overview:
- Purpose of the changes
- Scope and impact
- Files modified

### Security Review

Checks for common issues:
- Input validation
- Authentication/authorization
- SQL injection risks
- XSS vulnerabilities
- Hardcoded secrets

### Performance Review

Identifies potential issues:
- Database query efficiency
- Memory usage patterns
- Algorithmic complexity
- Resource handling

### Best Practices

Evaluates code quality:
- Error handling
- Code organization
- Documentation
- Test coverage

## Output Formats

### GitHub Format (Default)

```bash
ai github "PR_URL" --target github
```

Produces markdown suitable for GitHub comments:
- Proper heading hierarchy
- Code blocks with syntax highlighting
- Checkbox lists

### Slack Format

```bash
ai github "PR_URL" --target slack
```

Optimized for Slack:
- Simplified markdown
- Emoji indicators
- Compact layout

## Workflow Integration

### Pre-Merge Review

```bash
# Review before approving
ai github "PR_URL"

# Check the recommendations section
# Address any security concerns
```

### Team Sharing

```bash
# Generate Slack-friendly output
ai github "PR_URL" --target slack

# Copy and paste to team channel
```

### Documentation

```bash
# Save review for records
ai github "PR_URL" > pr-123-review.md
```

## Best Practices

### When to Use

- **Before approving** - Catch issues early
- **Complex PRs** - Get a second opinion
- **Security-sensitive code** - Extra scrutiny
- **Onboarding** - Learn codebase patterns

### Interpreting Results

| Indicator | Meaning |
|-----------|---------|
| ✅ | No issues found |
| ⚠️ | Potential concern, review needed |
| ❌ | Issue found, should be addressed |

### Taking Action

1. **Critical issues** - Request changes
2. **Warnings** - Discuss with author
3. **Suggestions** - Consider for future

## Troubleshooting

### "Authentication failed"

Your GitHub token may be invalid or expired.

```bash
# Check token is set
echo $GITHUB_TOKEN_WORK

# Verify token has correct scopes (repo, read:org)
```

See [Configuration](../getting-started/configuration.md#github-token).

### "Rate limit exceeded"

GitHub API has rate limits.

**Solutions:**
- Wait an hour for limits to reset
- Use a token with higher limits
- Reduce frequency of requests

### "Repository not found"

**Check:**
- URL is correct
- You have access to the repo
- Token has `repo` scope for private repos

## Related

- [github command](../commands/github.md) - Command reference
- [Configuration](../getting-started/configuration.md) - GitHub token setup
- [Commands Reference](../commands/README.md) - All commands
