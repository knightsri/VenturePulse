# VenturePulse Legacy Versions

This directory contains archived legacy versions of VenturePulse that have been superseded by the Docker-based V2 web application.

## Contents

### `streamlit/`
Standalone Streamlit web UI (single Python file, no authentication, file-based storage).

### `cli/`
Bash CLI scripts for command-line analysis (requires curl, jq).

## Why Archived?

These versions:
- May not work correctly with current prompt structure
- Lack authentication and multi-user support
- Don't have cost tracking or comparison features
- Are not actively maintained

## Current Version

For the current, maintained version, see the [main README](../README.md) and use:

```bash
docker-compose up
```
