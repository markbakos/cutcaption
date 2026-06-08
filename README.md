# cutcaption

Fast, local, open-source CLI/TUI for generating styled, burned-in, CapCut-like captions for one or many videos.

Core promise:

> One command. Pretty captions. Batch videos. No editing software.

This repository is currently in the foundation stage. The package layout, CLI shell, and test baseline are in place; transcription, caption styling, rendering, and TUI workflows will be added behind explicit service boundaries.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Run the CLI:

```bash
cutcaption --help
python -m cutcaption --version
```

Without installing the package, run from a source checkout with:

```bash
PYTHONPATH=src python -m cutcaption --help
```
