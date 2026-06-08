# cutcaption

Fast, local, open-source CLI for generating styled, burned-in, CapCut-like captions for one or many videos.

Core promise:

> One command. Pretty captions. Batch videos. No editing software.

This repository is currently in the foundation stage. The package layout, CLI shell, config validation, path discovery, caption chunking, and subtitle exporters are in place. Heavy media work is isolated behind transcription, probing, and rendering modules.

## Target UX

```bash
pipx install cutcaption
cutcaption video.mp4
cutcaption ./videos --preset shorts --style pop
cutcaption video.mp4 --srt
cutcaption video.mp4 --burn
cutcaption doctor
```

Defaults are creator-focused:

- input can be one video file or a folder of videos
- folder mode writes to `./captioned` unless `--output` is passed
- outputs default to `.srt` and burned-in `_captioned.mp4`
- default preset is `shorts`
- default style is `clean`
- default model is `small`
- default mode is `balanced`
- language is auto-detected unless `--language` is passed

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
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
