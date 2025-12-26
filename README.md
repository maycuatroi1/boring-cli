# Boring CLI

[![PyPI version](https://badge.fury.io/py/boring-cli.svg)](https://badge.fury.io/py/boring-cli)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CLI tool for managing Lark Suite tasks from the command line.

## Installation

```bash
pip install boring-cli
```

## Quick Start

### 1. Setup

Configure the CLI and login to Lark:

```bash
boring setup
```

This will prompt you for:
- Server URL (your Boring Agents API server)
- Bugs output directory (where tasks will be downloaded)
- Lark task list GUIDs
- Lark OAuth login

### 2. Download Tasks

Download tasks with Critical/Blocked/High labels to your local folder:

```bash
boring download
```

Download with specific labels:

```bash
boring download --labels "Critical,Blocked"
```

### 3. Solve Tasks

Move completed tasks (from your bugs folder) to the Solved section in Lark:

```bash
boring solve
```

Keep local folders after solving:

```bash
boring solve --keep
```

### 4. Check Status

View your current configuration:

```bash
boring status
```

## Commands

| Command | Description |
|---------|-------------|
| `boring setup` | Configure CLI and login to Lark |
| `boring download` | Download tasks to local folder |
| `boring solve` | Move tasks to Solved section |
| `boring status` | Show current configuration |
| `boring --version` | Show version |
| `boring --help` | Show help |

## Configuration

Configuration is stored in `~/.boring-agents/config.yaml`:

```yaml
server_url: https://boring.omelet.tech/api
jwt_token: eyJhbGc...
bugs_dir: /path/to/bugs
tasklist_guid: xxxx-xxxx-xxxx
section_guid: xxxx-xxxx-xxxx
solved_section_guid: xxxx-xxxx-xxxx
```

## Requirements

- Python 3.9+
- A running [Boring Agents](https://github.com/anhbinhnguyen/boring-agents) server

## Development

```bash
# Clone the repo
git clone https://github.com/anhbinhnguyen/boring-cli.git
cd boring-cli

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## License

MIT
