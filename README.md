# YouTube MP3 Downloader

A Python CLI application that downloads YouTube videos as MP3 files.

## Features

- Download audio from a single YouTube video
- Download audio from an entire YouTube playlist
- Automatic 1-minute delay between playlist downloads to avoid rate limiting
- Progress bar for downloads
- High-quality MP3 extraction

## Installation

1. Make sure you have Python 3.12 installed (this project uses a conda environment)
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Download a single video

```bash
python youtube_mp3.py download --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download a playlist

```bash
python youtube_mp3.py download --url "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### Specify output directory

```bash
python youtube_mp3.py download --url "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir "path/to/directory"
```

### Change the delay between playlist downloads

```bash
python youtube_mp3.py download --url "https://www.youtube.com/playlist?list=PLAYLIST_ID" --delay 30
```

## Requirements

- Python 3.12
- yt-dlp (a more reliable YouTube downloader)
- click (for CLI interface)
- tqdm (for progress bars)

## How It Works

This application uses yt-dlp to download YouTube videos and extract their audio in MP3 format. When downloading playlists, it automatically adds a delay between downloads to avoid rate limiting by YouTube.
