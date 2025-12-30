# Configuration

[Home](../README.md) > [Getting Started](README.md) > Configuration

## Environment Variables

The CLI tools use environment variables for API keys and configuration.

### Required Variables

| Variable | Description | Used By |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | All LLM features |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | All LLM features |

You need at least one LLM provider key.

### Optional Variables

| Variable | Description | Used By |
|----------|-------------|---------|
| `YOUTUBE_API_KEY` | YouTube Data API key | [process-playlist](../commands/process-playlist.md) |
| `GITHUB_TOKEN_WORK` | GitHub personal access token | [github](../commands/github.md) |
| `SLACK_TOKEN` | Slack API token | Slack integrations |

## Setting Environment Variables

### Temporary (Current Session)

```bash
export DEEPSEEK_API_KEY="your_key"
export YOUTUBE_API_KEY="your_key"
```

### Permanent (Add to Shell Config)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# CLI Tools API Keys
export DEEPSEEK_API_KEY="your_deepseek_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
export YOUTUBE_API_KEY="your_youtube_key"
export GITHUB_TOKEN_WORK="your_github_token"
```

Then reload:

```bash
source ~/.bashrc
```

## LLM Providers

### DeepSeek (Recommended for Cost)

```bash
ai youtube "URL" --llm-provider deepseek
```

- Lower cost per token
- Good quality for most tasks
- Get key at: https://platform.deepseek.com/

### Anthropic Claude

```bash
ai youtube "URL" --llm-provider anthropic
```

- Higher quality analysis
- More expensive
- Get key at: https://console.anthropic.com/

### Default Provider

The default provider is `anthropic`. Override with `--llm-provider`:

```bash
ai youtube "URL" --llm-provider deepseek
```

## Getting API Keys

### YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable "YouTube Data API v3"
4. Create credentials > API Key
5. Copy the key

### GitHub Token

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`
4. Copy the token

### DeepSeek API Key

1. Go to [DeepSeek Platform](https://platform.deepseek.com/)
2. Sign up / Log in
3. Navigate to API Keys
4. Create new key

### Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up / Log in
3. Navigate to API Keys
4. Create new key

## Verifying Configuration

Check your environment variables:

```bash
# Should print your keys (don't share these!)
echo $DEEPSEEK_API_KEY
echo $YOUTUBE_API_KEY
echo $GITHUB_TOKEN_WORK
```

Test a command:

```bash
ai youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --llm-provider deepseek
```

## Related

- [Quick Start](quick-start.md) - First commands
- [youtube command](../commands/youtube.md) - Uses LLM providers
- [process-playlist command](../commands/process-playlist.md) - Uses YouTube API
- [github command](../commands/github.md) - Uses GitHub token
