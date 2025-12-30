# Installation

[Home](../README.md) > [Getting Started](README.md) > Installation

## Docker Installation (Recommended)

The CLI tools run in Docker containers, so you don't need to install Python dependencies locally.

### 1. Clone the Repository

```bash
git clone https://github.com/ersantana361/cli_tools.git
cd cli_tools
```

### 2. Build the Docker Image

```bash
docker-compose build
```

This builds the `cli_tools-ai-tools-api` image with all dependencies.

### 3. Verify the Build

```bash
./docker-run.sh --help
```

You should see the available commands: `convert`, `github`, `youtube`, `process-playlist`.

## Local Installation (Alternative)

If you prefer running without Docker:

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Commands

```bash
python ai_tools/main.py --help
```

## Updating

To update to the latest version:

```bash
git pull
docker-compose build
```

## Troubleshooting

### Docker image not found

If you see "Docker image not found", the `docker-run.sh` script will automatically build it:

```bash
./docker-run.sh youtube --help
# [WARNING] Docker image not found. Building it now...
```

### Permission denied

Make sure `docker-run.sh` is executable:

```bash
chmod +x docker-run.sh
```

### Docker daemon not running

Start Docker Desktop or the Docker service:

```bash
# Linux
sudo systemctl start docker

# Mac/Windows
# Open Docker Desktop application
```

## Next Steps

- [Quick Start](quick-start.md) - Set up the alias and run commands
- [Configuration](configuration.md) - Add your API keys

## Related

- [Commands Reference](../commands/README.md)
- [API Reference](../api/README.md)
