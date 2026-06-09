# cutcaption

**cutcaption — CapCut-like captions from your terminal**

Generate clean, styled, burned-in captions for one video or a folder of videos using faster-whisper.

```bash
pipx install cutcaption
cutcaption video.mp4
```

By default, cutcaption transcribes your video, builds short creator-friendly captions, writes subtitles, and burns styled captions into a new video.

## Quick Start

```bash
cutcaption video.mp4
cutcaption ./videos --preset shorts --style pop
cutcaption video.mp4 --srt --no-burn
cutcaption doctor
```

Common outputs:

- `video.srt` for standard subtitles
- `video.ass` when styled captions are needed for burning
- `video.json` when JSON metadata is enabled
- `video_captioned.mp4` for the burned-in captioned video

For folders, cutcaption writes to a `captioned/` folder unless you pass `--output`.

## Install

If you already have `pipx`:

```bash
pipx install cutcaption
```

If you do not have `pipx` yet, install it first.

macOS/Linux:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install cutcaption
```

Windows:

```bash
py -m pip install --user pipx
py -m pipx ensurepath
pipx install cutcaption
```

Then restart your terminal if needed and run:

```bash
cutcaption video.mp4
```

Alternative: install with `pip`.

macOS/Linux:

```bash
python3 -m pip install --user cutcaption
cutcaption video.mp4
```

Windows:

```bash
py -m pip install --user cutcaption
cutcaption video.mp4
```

Requirements:

- Python 3.10+
- `ffmpeg` and `ffprobe` for burned-in captions and media probing
- faster-whisper model files download on first use

## Development Install

```bash
git clone https://github.com/your-org/cutcaption.git
cd cutcaption
pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest
python -m ruff check .
```

## Usage

Caption one video:

```bash
cutcaption video.mp4
```

Choose an output folder:

```bash
cutcaption video.mp4 --output ./out
```

Caption a folder:

```bash
cutcaption ./videos --output ./captioned
```

Caption a folder recursively:

```bash
cutcaption ./videos --recursive
```

Export subtitles without rendering a video:

```bash
cutcaption video.mp4 --srt --ass --no-burn
```

Write JSON metadata:

```bash
cutcaption video.mp4 --json
```

Replace existing outputs:

```bash
cutcaption video.mp4 --overwrite
```

Preview planned jobs without transcription:

```bash
cutcaption ./videos --dry-run
```

## Batch Examples

Fast batch captions for short-form clips:

```bash
cutcaption ./clips --preset shorts --style pop --recursive
```

Create only subtitle files for a batch:

```bash
cutcaption ./clips --srt --ass --no-burn
```

Skip files that already have requested outputs:

```bash
cutcaption ./clips --skip-existing
```

Force regeneration:

```bash
cutcaption ./clips --overwrite
```

`--jobs` is accepted for future parallel processing. Processing is currently sequential.

## Styles

List available styles:

```bash
cutcaption styles
```

Examples:

```bash
cutcaption video.mp4 --style clean
cutcaption video.mp4 --style bold
cutcaption video.mp4 --style pop
cutcaption video.mp4 --style minimal
cutcaption video.mp4 --style boxed
cutcaption video.mp4 --style shorts
```

Style guide:

- `clean`: readable white text, moderate outline, no box
- `bold`: larger uppercase captions with thicker outline
- `pop`: big creator-style uppercase captions with thick outline and shadow
- `minimal`: smaller captions with a thin outline
- `boxed`: readable text over a semi-transparent box
- `shorts`: one spoken word at a time for fast short-form videos

## Presets

```bash
cutcaption video.mp4 --preset shorts
cutcaption video.mp4 --preset youtube
cutcaption video.mp4 --preset podcast
cutcaption video.mp4 --preset default
```

`shorts` is the default and is tuned for short creator videos.

## Config File

Create a starter config:

```bash
cutcaption init
```

Use a config file:

```bash
cutcaption video.mp4 --config cutcaption.toml
```

Example:

```toml
output = "captioned"

[transcription]
model = "small"
mode = "balanced"
language = "" # auto
device = "auto"
compute_type = "auto"

[caption]
preset = "shorts"
style = "pop"
max_words = 5
max_lines = 2
min_caption_duration = 0.25
max_caption_duration = 2.5

[render]
burn = true
srt = true
ass = false
json = true

[batch]
recursive = false
skip_existing = true
overwrite = false
jobs = 1
```

See [examples/cutcaption.toml](examples/cutcaption.toml).

## Doctor

Check local tools and dependencies:

```bash
cutcaption doctor
```

Use this first when rendering or transcription fails.

## Troubleshooting

### ffmpeg not found

Install ffmpeg and make sure `ffmpeg` and `ffprobe` are on your `PATH`.

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
winget install Gyan.FFmpeg
```

Then run:

```bash
cutcaption doctor
```

### Model download is slow

faster-whisper downloads the selected model on first use. The first run can take longer depending on model size and network speed. Use a smaller model for quicker startup:

```bash
cutcaption video.mp4 --model small --mode fast
```

### CUDA is not working

CPU transcription works by default. If CUDA setup is unreliable, use the default device or force CPU in your config:

```toml
[transcription]
device = "cpu"
compute_type = "int8"
```

Run:

```bash
cutcaption doctor
```

### Output already exists

By default, cutcaption skips existing requested outputs in batch mode. To regenerate files:

```bash
cutcaption video.mp4 --overwrite
```

To fail instead of skipping existing files:

```bash
cutcaption video.mp4 --no-skip-existing
```

## Roadmap

- Parallel batch processing
- Live style preview
- More caption animation presets
- Current-word highlighting
- GPU setup helpers
- More export formats

## Contributing

Contributions are welcome. For local work:

```bash
pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

Keep changes focused, add tests for behavior changes, and update docs when user-facing commands or config options change.

## License

MIT. See [LICENSE](LICENSE).
