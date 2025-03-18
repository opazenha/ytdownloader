#!/usr/bin/env python3
"""
YouTube MP3 Downloader - A CLI tool to download YouTube videos as MP3 files.
"""

import os
import time
import click
import re
import sys
import logging
import json
import subprocess
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if yt-dlp is installed
try:
    subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, check=True)
except (subprocess.SubprocessError, FileNotFoundError):
    logger.error("yt-dlp is not installed or not in PATH. Please install it with: pip install yt-dlp")
    sys.exit(1)

def sanitize_filename(filename):
    """Remove invalid characters from filename."""
    if not filename:
        return "unknown_title"
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_video_info(url):
    """Get video information using yt-dlp."""
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--no-playlist',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        video_info = json.loads(result.stdout)
        return video_info
    except subprocess.SubprocessError as e:
        logger.error(f"Error getting video info: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing video info: {str(e)}")
        return None

def get_playlist_info(url):
    """Get playlist information using yt-dlp."""
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--flat-playlist',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse each line as a separate JSON object
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video_info = json.loads(line)
                    videos.append(video_info)
                except json.JSONDecodeError:
                    pass
        
        return videos
    except subprocess.SubprocessError as e:
        logger.error(f"Error getting playlist info: {str(e)}")
        return []

def download_audio(url, output_dir=None):
    """Download audio from a YouTube video using yt-dlp."""
    try:
        # Get video info first to get the title
        video_info = get_video_info(url)
        if not video_info:
            logger.error(f"Could not get video info for {url}")
            return False
        
        video_title = video_info.get('title', '')
        if not video_title:
            video_id = video_info.get('id', 'unknown')
            video_title = f"youtube_video_{video_id}"
        
        sanitized_title = sanitize_filename(video_title)
        logger.info(f"Downloading: {video_title}")
        
        # Create output directory if it doesn't exist
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "downloads")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Set the output file path
        output_path = os.path.join(output_dir, f"{sanitized_title}.mp3")
        
        # Check if file already exists
        if os.path.exists(output_path):
            logger.info(f"File already exists: {output_path}")
            return True
        
        # Download the audio file
        cmd = [
            'yt-dlp',
            '-f', 'bestaudio',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality
            '-o', f"{output_dir}/{sanitized_title}.%(ext)s",
            '--no-playlist',
            '--progress',
            url
        ]
        
        process = subprocess.run(cmd, check=True)
        
        if process.returncode == 0:
            logger.info(f"Downloaded: {sanitized_title}.mp3")
            return True
        else:
            logger.error(f"Error downloading {url}: Process returned {process.returncode}")
            return False
    
    except subprocess.SubprocessError as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def download_playlist(playlist_url, output_dir=None, delay=60):
    """Download all videos from a YouTube playlist as MP3 files."""
    try:
        # Get playlist information
        videos = get_playlist_info(playlist_url)
        
        if not videos:
            logger.error(f"No videos found in playlist: {playlist_url}")
            return False
        
        logger.info(f"Playlist: {playlist_url}")
        logger.info(f"Number of videos: {len(videos)}")
        
        # Create a progress bar
        with tqdm(total=len(videos), desc="Downloading playlist") as pbar:
            for i, video_info in enumerate(videos):
                video_url = f"https://www.youtube.com/watch?v={video_info.get('id', '')}" 
                logger.info(f"Processing video {i+1}/{len(videos)}: {video_info.get('title', 'Unknown title')}")
                
                success = download_audio(video_url, output_dir)
                pbar.update(1)
                
                # Add delay between downloads (except for the last video)
                if i < len(videos) - 1 and success:
                    logger.info(f"Waiting {delay} seconds before next download...")
                    for remaining in range(delay, 0, -1):
                        if remaining % 10 == 0:  # Only log every 10 seconds
                            logger.info(f"Waiting {remaining} more seconds...")
                        time.sleep(1)
        
        logger.info("Playlist download completed!")
        return True
    
    except Exception as e:
        logger.error(f"Error downloading playlist: {str(e)}")
        return False

@click.group()
def cli():
    """YouTube MP3 Downloader CLI."""
    pass

@cli.command()
@click.option('--url', required=True, help='YouTube video or playlist URL')
@click.option('--output-dir', default=None, help='Directory to save the downloaded files')
@click.option('--delay', default=60, help='Delay in seconds between playlist downloads')
def download(url, output_dir, delay):
    """Download audio from YouTube video or playlist."""
    if "playlist" in url or "list=" in url:
        logger.info("Detected playlist URL")
        download_playlist(url, output_dir, delay)
    else:
        logger.info("Detected single video URL")
        download_audio(url, output_dir)

if __name__ == '__main__':
    cli()
