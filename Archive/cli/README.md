# VenturePulse CLI Version (Legacy)

> **Note:** This is the archived legacy CLI. The main project has moved to a Docker-based web application. See the [main README](../../README.md) for the current version.

## About This Version

These Bash scripts were the original command-line interface for VenturePulse. They're preserved here for reference but may not work correctly with the current prompt structure.

## Scripts

- **`analyze-script.sh`** - Main orchestrator
- **`call-openrouter.sh`** - OpenRouter API wrapper
- **`create-wrapper.sh`** - HTML wrapper generation
- **`generate-provenance.sh`** - Metadata/provenance generation
- **`createindex.py`** - Index page generator

## Usage (May Not Work)

```bash
# Set API key
export OPENROUTER_API_KEY="your_key_here"

# Run analysis
./analyze-script.sh <project-file.md> [model-name]

# Example
./analyze-script.sh ../../examples/sample-project/smartplate-idea.md anthropic/claude-sonnet-4
```

## Requirements

- Bash (Mac/Linux/WSL/Git Bash)
- `curl`, `jq`, `sed`, `mktemp`
- OpenRouter API key

## Why It Was Archived

The CLI version:
- Only supports 8 sections (vs 19 in web app)
- No authentication or user management
- No cost tracking
- No multi-model comparison
- Prompts have evolved and may not work correctly

For current usage, use the Docker web application.
