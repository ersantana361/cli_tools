# ngit-tidy 🧹🚀

A Git extension that automatically splits unstaged changes into structured commits, separating code tidying from functional changes.

## Key Features

- **Non-Destructive** - Never modifies existing commits
- **Context-Aware** - AST-based change classification
- **Interactive** - Rich terminal UI for manual review
- **Safe** - Automatic backups before any changes

## Installation

```bash
git clone https://github.com/yourusername/ngit-tidy.git
cd ngit-tidy
pip install -r requirements.txt
```

## How It Works

### Basic Flow
1. **Input**: Unstaged changes in working directory
2. **Analysis**:
   ```mermaid
   flowchart TD
       A[Unstaged Changes] --> B[Parse AST]
       B --> C{Structural?}
       C -->|Yes| D[🧹 Tidy Commit]
       C -->|No| E[🚀 Feature Commit]
   ```
3. **Output**: New commits preserving original change order

### Key Behaviors
- **Staging Area**: Leaves staged changes untouched
- **Safety Net**: Creates `refs/gittidy-backup` before operations
- **Cleanup**: Resets working directory after commit creation

```bash
# Before
❯ git status
Changes not staged for commit:
  modified:   app.py
  modified:   utils.py

# After running ngit-tidy
❯ git log --oneline
abcd123 (HEAD) 🚀 Add user auth flow
7890efg 🧹 Rename service classes
```

## Usage

```bash
# Auto-classify changes in current directory
ngit tidy

# Interactive review with atomic commits
ngit tidy -i -g atomic

# Analyze specific repository
ngit tidy ~/projects/myapp -l python
```

## Command Reference

```text
❯ ngit tidy --help
usage: ngit tidy [-h] [-i] [-g {atomic,category}] [-l {python,js}] [path]

Transform working directory changes into structured commits

Process Flow:
1. Analyzes UNSTAGED changes
2. Classifies as structural/behavioral
3. Creates new commits
4. Resets working directory

positional arguments:
  path                  Git repository path (default: current directory)

options:
  -h, --help            show this help message and exit
  -i, --interactive     Step through each change with visual confirmation
  -g {atomic,category}, --granularity {atomic,category}
                        Commit grouping:
                          atomic - One commit per change
                          category - Group by type (default)
  -l {python,js}, --language {python,js}
                        Analysis language (default: python)

Recovery:
  If interrupted, use `git reset --hard refs/gittidy-backup`
  View backup reference: `git show refs/gittidy-backup`

Examples:
  ngit tidy              # Auto-classify current dir changes
  ngit tidy -i ~/src     # Interactive review of ~/src repo
```

## FAQ

**Q: What happens to my staged changes?**<br>
A: They remain staged - ngit-tidy only processes unstaged changes.

**Q: Can I use this on partial files?**<br>
A: Yes! Stage some hunks with `git add -p` first, then process the rest.

**Q: How is this different from `git commit -p`?**<br>
A: ngit-tidy understands code semantics rather than just diffs, and creates properly separated commits.

**Q: What if I change my mind after running?**<br>
A: Use `git reset --keep HEAD~2` to undo (assuming 2 new commits created).
