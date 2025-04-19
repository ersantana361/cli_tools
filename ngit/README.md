# ngit-tidy 🧹🚀

A Git extension with AI-powered commit messages for structured workflows.

## Key Features

- **AI Commit Messages** - Generate semantic messages with `--ai`
- **Safety First** - Automatic backups before any changes
- **Multi-Language** - Python & JavaScript support
- **Interactive Review** - Rich terminal interface

## Installation

```bash
git clone https://github.com/yourusername/ngit-tidy.git
cd ngit-tidy
pip install -r requirements.txt
export DEEPSEEK_API_KEY='your-api-key'  # For AI features
```

## AI-Powered Usage

```bash
# Generate commits with AI messages
ngit tidy --ai

# Interactive AI mode
ngit tidy --ai -i

# Example output
feat(auth): implement OAuth2 token refresh
- Add token rotation security pattern
- Handle expiry edge cases
```

## Command Reference

```text
❯ ngit tidy --help

Options:
  --ai            Generate commit messages using LLM
  -i, --interactive  Step through changes interactively
  -g {atomic,category}  Commit grouping strategy
  -l {python,js}  Analysis language

AI Requirements:
  - DEEPSEEK_API_KEY environment variable
  - Internet connection
```

## FAQ

**Q: How does the AI message generation work?**  
A: Uses DeepSeek's API to analyze diffs and follow conventional commit guidelines.

**Q: Is my code sent to external servers?**  
A: Yes - when using `--ai`, diffs are sent to DeepSeek's API.

**Q: Can I use a different LLM?**  
A: Currently supports DeepSeek - OpenAI support coming soon.

**Q: What if AI generation fails?**  
A: Falls back to simple "Structural changes" messages automatically.
