# Boring CLI

[![PyPI version](https://badge.fury.io/py/boring-cli.svg)](https://badge.fury.io/py/boring-cli)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CLI tool for managing Lark Suite bug tasks from the command line.

## Installation

```bash
pip install boring-cli
```

## Quick Start Guide

### Step 1: Run Setup

```bash
boring setup
```

### Step 2: Configure Settings

You'll be prompted for the following settings:

```
Server URL [https://boring.omelet.tech/api]: (press Enter to use default)
Bugs output directory [/tmp/bugs]: /path/to/your/project/bugs
Tasklist GUID (from Lark) []: 9a31701d-fd0e-4417-b00d-e040afe2b234
In-progress Section GUID []: e2c8e412-fbae-41ea-9daa-c2b58efc1b87
Solved Section GUID []: 76a74fd6-79d8-4f74-a358-e78c688ee5ef
```

**Default GUIDs for Bugs list:**
| Setting | GUID |
|---------|------|
| Tasklist GUID | `9a31701d-fd0e-4417-b00d-e040afe2b234` |
| In-progress Section (Inprogress - Bình) | `e2c8e412-fbae-41ea-9daa-c2b58efc1b87` |
| Solved Section | `76a74fd6-79d8-4f74-a358-e78c688ee5ef` |

### Step 3: Login with Lark

1. A browser window will open for Lark login
2. Login with your Lark account
3. After login, you'll see a JSON response like:
   ```json
   {"user":{...},"token":{"access_token":"eyJhbGciOiJ...",...}}
   ```
4. Copy the `access_token` value (the long string starting with `eyJ...`)
5. Paste it in the terminal when prompted

```
Paste your access_token here: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Login successful!
Setup complete!
```

### Step 4: Download Bug Tasks

Download all tasks from your configured section:

```bash
boring download
```

Download to a specific directory:

```bash
boring download --dir /path/to/your/project/bugs
```

Download from a specific section:

```bash
boring download --section e2c8e412-fbae-41ea-9daa-c2b58efc1b87
```

### Step 5: View Sections (Optional)

List all tasklists and sections to find GUIDs:

```bash
boring sections
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `boring setup` | Configure CLI and login to Lark |
| `boring download` | Download tasks to local folder |
| `boring download --section GUID` | Download from specific section |
| `boring download --dir PATH` | Download to specific directory |
| `boring download --labels "Critical,High"` | Filter by labels |
| `boring sections` | List all tasklists and sections |
| `boring solve` | Move tasks to Solved section |
| `boring solve --keep` | Solve but keep local folders |
| `boring status` | Show current configuration |
| `boring --version` | Show version |
| `boring --help` | Show help |

## Configuration File

Configuration is stored in `~/.boring-agents/config.yaml`:

```yaml
server_url: https://boring.omelet.tech/api
jwt_token: eyJhbGc...
bugs_dir: /path/to/your/project/bugs
tasklist_guid: 9a31701d-fd0e-4417-b00d-e040afe2b234
section_guid: e2c8e412-fbae-41ea-9daa-c2b58efc1b87
solved_section_guid: 76a74fd6-79d8-4f74-a358-e78c688ee5ef
```

## Troubleshooting

### Token Expired
If you see authentication errors, run `boring setup` again to get a new token.

### Find Section GUIDs
Run `boring sections` to list all available tasklists and their sections with GUIDs.

## Requirements

- Python 3.9+

## License

MIT
