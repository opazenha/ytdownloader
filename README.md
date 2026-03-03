# YouTube Downloader

A Python CLI application that downloads YouTube videos as MP3 (default) or compressed MP4 files.

## Features

- Download audio from a single YouTube video
- Download audio from an entire YouTube playlist
- Download compressed MP4 for a single video or playlist
- Automatic delay between playlist downloads to avoid rate limiting
- Progress bar for downloads
- High-quality MP3 extraction
- Smart default output folders:
  - `downloads/` for MP3
  - `videos/` for MP4

## Installation

1. Make sure you have Python 3.12 installed (this project uses a conda environment)
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Download a single video (MP3, default)

```bash
python youtube_mp3.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download a playlist

```bash
python youtube_mp3.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### Specify output directory

```bash
python youtube_mp3.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir "path/to/directory"
```

### Download compressed MP4

```bash
# Download one video as MP4 to ./videos
python youtube_mp3.py "https://www.youtube.com/watch?v=VIDEO_ID" --media-type video

# Download playlist as MP4, every file resized to <= 360p and higher compression
python youtube_mp3.py "https://www.youtube.com/playlist?list=PLAYLIST_ID" --media-type video --max-height 360 --crf 34 --video-bitrate 600k --audio-bitrate 96k
```

### Change the delay between playlist downloads

```bash
python youtube_mp3.py "https://www.youtube.com/playlist?list=PLAYLIST_ID" --delay 30
```

### Compression options (MP4)

```bash
python youtube_mp3.py "https://www.youtube.com/watch?v=VIDEO_ID" \
  --media-type video \
  --max-height 480 \
  --crf 32 \
  --video-bitrate 900k \
  --audio-bitrate 128k
```

- `max-height`: limits resolution height (e.g. 480)
- `crf`: x264 quality/size tradeoff (higher = smaller file)
- `video-bitrate`: target video bitrate
- `audio-bitrate`: target audio bitrate

## Requirements

- Python 3.12
- yt-dlp (a more reliable YouTube downloader)
- click (for CLI interface)
- tqdm (for progress bars)

## How It Works

This application uses `yt-dlp` to download YouTube videos either as MP3 files (default) or compressed MP4 files. For long tutorials, use `--media-type video` with `--max-height` and `--crf` tuned for smaller file sizes.
