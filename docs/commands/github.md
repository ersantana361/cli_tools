# github Command

[Home](../README.md) > [Commands](README.md) > github

Analyze GitHub pull requests using AI to generate reviews, summaries, and insights.

## Usage

```bash
ai github "PR_URL" [options]
```

## Examples

### Basic Analysis

```bash
ai github "https://github.com/owner/repo/pull/123"
```

Analyzes the PR and outputs a GitHub-formatted review.

### Slack Output

```bash
ai github "https://github.com/owner/repo/pull/123" --target slack
```

Formats the output for Slack posting.

### Using DeepSeek

```bash
ai github "https://github.com/owner/repo/pull/123" --llm-provider deepseek
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--target` | Output format (`github`/`slack`) | `github` |
| `--llm-provider` | LLM provider (`anthropic`/`deepseek`) | `anthropic` |

## Requirements

Set the `GITHUB_TOKEN_WORK` environment variable:

```bash
export GITHUB_TOKEN_WORK="your_github_token"
```

See [Configuration](../getting-started/configuration.md#github-token) for setup.

## Output

The analysis includes:

### Summary
- Overall assessment of the PR
- Key changes identified
- Scope and impact

### Code Review
- Security considerations
- Performance implications
- Best practices compliance
- Potential issues

### Recommendations
- Suggested improvements
- Questions for the author
- Approval/revision recommendation

## Output Formats

### GitHub Format

```markdown
## PR Analysis

### Summary
This PR implements user authentication...

### Security Review
- ✅ Input validation present
- ⚠️ Consider rate limiting on login endpoint

### Recommendations
1. Add tests for edge cases
2. Update documentation
```

### Slack Format

Optimized for Slack with:
- Simplified markdown
- Emoji indicators
- Compact layout

## How It Works

1. **Fetch PR Data** - Uses GitHub API to get PR details, diff, and comments
2. **Analyze Changes** - Sends diff to LLM for review
3. **Generate Report** - Structures findings into readable format
4. **Output** - Displays or copies formatted review

## Troubleshooting

### "Authentication failed"

Check your GitHub token:

```bash
echo $GITHUB_TOKEN_WORK
```

Make sure the token has `repo` and `read:org` scopes.

### "PR not found"

Verify:
- The URL is correct
- You have access to the repository
- The PR number exists

### Rate limiting

GitHub API has rate limits. If you hit them, wait a few minutes or use a token with higher limits.

## Related

- [PR Review Guide](../guides/pr-review.md) - In-depth PR review workflows
- [Configuration](../getting-started/configuration.md) - API keys setup
- [Commands Reference](README.md) - All commands
