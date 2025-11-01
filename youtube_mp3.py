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
import asyncio
import requests
from tqdm import tqdm
from groq import Groq
import eyed3

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def send_telegram_message(message):
    """Send a message via Telegram bot."""
    try:
        bot_token = os.environ.get("ZENHA_TELEGRAM_TOKEN")
        chat_id = os.environ.get("ZENHA_TELEGRAM_CHAT_ID", "7996278878")
        
        if not bot_token:
            logger.warning("⚠️ ZENHA_TELEGRAM_TOKEN not found. Skipping Telegram notification.")
            return False
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        
        logger.info("📱 Telegram notification sent successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send Telegram notification: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending Telegram notification: {str(e)}")
        return False

# Check if yt-dlp is installed
try:
    subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, check=True)
except (subprocess.SubprocessError, FileNotFoundError):
    logger.error("❌ yt-dlp is not installed or not in PATH. Please install it with: pip install yt-dlp")
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
        logger.error(f"❌ Error getting video info: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing video info: {str(e)}")
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
        logger.error(f"❌ Error getting playlist info: {str(e)}")
        return []

def download_audio(url, output_dir=None, suppress_notification=False):
    """Download audio from a YouTube video using yt-dlp."""
    try:
        # Get video info first to get the title
        video_info = get_video_info(url)
        if not video_info:
            logger.error(f"❌ Could not get video info for {url}")
            return False
        
        video_title = video_info.get('title', '')
        if not video_title:
            video_id = video_info.get('id', 'unknown')
            video_title = f"youtube_video_{video_id}"
        
        sanitized_title = sanitize_filename(video_title)
        logger.info(f"⬇️  Downloading: {video_title}")
        
        # Create output directory if it doesn't exist
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "downloads")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Set the output file path
        output_path = os.path.join(output_dir, f"{sanitized_title}.mp3")
        
        # Check if file already exists
        if os.path.exists(output_path):
            logger.info(f"✅ File already exists: {output_path}")
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
            logger.info(f"✅ Downloaded: {sanitized_title}.mp3")
            
            # Wait a moment for file to be fully written
            time.sleep(1)
            
            # Check if the final MP3 file exists
            final_mp3_path = output_path  # The output_path should already be the correct .mp3 file
            if os.path.exists(final_mp3_path):
                # Update metadata using API
                title, artist = process_metadata(video_title)
                if title and artist:
                    update_mp3_metadata(final_mp3_path, title, artist)
                
                # Sync to Navidrome asynchronously
                asyncio.run(sync_to_navidrome(final_mp3_path))
                
                # Send Telegram notification (only if not suppressed)
                if not suppress_notification:
                    send_telegram_message(f"✅ <b>Download Completed!</b>\n\n🎵 {video_title}\n📁 Saved to: {output_path}\n🔄 Synced to Navidrome")
            else:
                logger.warning(f"⚠️  MP3 file not found at expected path: {final_mp3_path}")
            
            return True
        else:
            logger.error(f"❌ Error downloading {url}: Process returned {process.returncode}")
            return False
    
    except subprocess.SubprocessError as e:
        logger.error(f"❌ Error downloading {url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

def download_playlist(playlist_url, output_dir=None, delay=60):
    """Download all videos from a YouTube playlist as MP3 files."""
    try:
        # Get playlist information
        videos = get_playlist_info(playlist_url)
        
        if not videos:
            logger.error(f"❌ No videos found in playlist: {playlist_url}")
            return False
        
        logger.info(f"📋 Playlist: {playlist_url}")
        logger.info(f"🎵 Number of videos: {len(videos)}")
        
        # Create a progress bar
        with tqdm(total=len(videos), desc="Downloading playlist") as pbar:
            for i, video_info in enumerate(videos):
                video_url = f"https://www.youtube.com/watch?v={video_info.get('id', '')}" 
                logger.info(f"🎬 Processing video {i+1}/{len(videos)}: {video_info.get('title', 'Unknown title')}")
                
                success = download_audio(video_url, output_dir, suppress_notification=True)
                pbar.update(1)
                
                # Add delay between downloads (except for the last video)
                if i < len(videos) - 1 and success:
                    logger.info(f"⏳ Waiting {delay} seconds before next download...")
                    for remaining in range(delay, 0, -1):
                        if remaining % 10 == 0:  # Only log every 10 seconds
                            logger.info(f"⏳ Waiting {remaining} more seconds...")
                        time.sleep(1)
        
        logger.info("🎉 Playlist download completed!")
        
        # Sync all downloaded files to Navidrome
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "downloads")
        
        logger.info("🔄 Syncing all downloaded files to Navidrome...")
        for filename in os.listdir(output_dir):
            if filename.endswith('.mp3'):
                file_path = os.path.join(output_dir, filename)
                asyncio.run(sync_to_navidrome(file_path))
        
        # Send Telegram notification
        send_telegram_message(f"✅ <b>Playlist Download Completed!</b>\n\n📁 Downloaded {len(videos)} videos\n🎵 Saved to: {output_dir}\n📊 All files synced to Navidrome")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error downloading playlist: {str(e)}")
        return False

def process_metadata(file_name):
    # Check if API key is available
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.warning("⚠️  GROQ_API_KEY not found. Using filename as fallback.")
        # Simple fallback: try to extract from filename
        if " - " in file_name:
            parts = file_name.split(" - ", 1)
            if len(parts) == 2:
                return parts[1].strip(), parts[0].strip()
        return file_name, "Unknown Artist"
    
    try:
        client = Groq(api_key=api_key)

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Extract the title and artist of the song out of the Youtube video title. Return the result as a JSON object with 'title' and 'artist' keys. Do NOT use markdown code blocks (```json) in your response - return only the raw JSON. Video title: {file_name}",
                }
            ],
            model="llama-3.1-8b-instant",
        )

        response_content = chat_completion.choices[0].message.content
        
        if response_content:
            try:
                # First attempt: parse directly
                metadata = json.loads(response_content)
                title = metadata.get('title', '')
                artist = metadata.get('artist', '')
                return title, artist
            except json.JSONDecodeError:
                # Second attempt: remove markdown code blocks and try again
                cleaned_response = response_content.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove closing ```
                cleaned_response = cleaned_response.strip()
                
                try:
                    metadata = json.loads(cleaned_response)
                    title = metadata.get('title', '')
                    artist = metadata.get('artist', '')
                    return title, artist
                except json.JSONDecodeError:
                    logger.error(f"❌ Failed to parse JSON response after cleaning: {response_content}")
                    return '', ''
        else:
            logger.error("❌ Empty response from API")
            return file_name, "Unknown Artist"

    except Exception as e:
        logger.error(f"❌ API call failed: {str(e)}. Using filename as fallback.")
        # Fallback to simple parsing
        if " - " in file_name:
            parts = file_name.split(" - ", 1)
            if len(parts) == 2:
                return parts[1].strip(), parts[0].strip()
        return file_name, "Unknown Artist"

def update_mp3_metadata(file_path, title, artist):
    """Update MP3 file metadata with title and artist."""
    try:
        logger.info(f"🏷️  Updating metadata for: {file_path}")
        logger.info(f"🎵 Title: '{title}', Artist: '{artist}'")
        
        audiofile = eyed3.load(file_path)
        if audiofile is None:
            logger.error(f"❌ Could not load MP3 file: {file_path}")
            return False
        
        if audiofile.tag is None:
            logger.info("🏷️  Initializing new tag")
            audiofile.initTag(version=(2, 4))
        
        audiofile.tag.title = title
        audiofile.tag.artist = artist
        
        # CRITICAL: Save the tag to disk
        audiofile.tag.save()  # type: ignore
        
        logger.info(f"✅ Successfully updated metadata for {file_path}: {title} - {artist}")
        return True
    except Exception as e:
        logger.error(f"❌ Error updating metadata for {file_path}: {str(e)}")
        return False

async def sync_to_navidrome(file_path):
    """Async function to sync file to VPS using rsync."""
    try:
        logger.info(f"🔄 Starting sync to Navidrome for: {file_path}")
        
        # Build the rsync command to sync the specific file
        rsync_cmd = f'rsync -avzP -e "ssh -i /home/zenha/.ssh/ocloud.key" "{file_path}" ubuntu@192.9.133.211:/home/ubuntu/navidrome/music/'
        
        # Run the rsync command asynchronously
        process = await asyncio.create_subprocess_shell(
            rsync_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info(f"✅ Successfully synced {file_path} to Navidrome")
            if stdout:
                logger.info(f"📤 Sync output: {stdout.decode().strip()}")
        else:
            logger.error(f"❌ Failed to sync {file_path} to Navidrome")
            if stderr:
                logger.error(f"❌ Sync error: {stderr.decode().strip()}")
        
        return process.returncode == 0
    except Exception as e:
        logger.error(f"❌ Error during Navidrome sync: {str(e)}")
        return False

@click.command()
@click.argument('url', required=True)
@click.option('--output-dir', default=None, help='Directory to save the downloaded files')
@click.option('--delay', default=20, help='Delay in seconds between playlist downloads')
def cli(url, output_dir, delay):
    """Download audio from YouTube video or playlist."""
    if "playlist" in url or "list=" in url:
        logger.info("📋 Detected playlist URL")
        success = download_playlist(url, output_dir, delay)
        if not success:
            send_telegram_message("❌ <b>Playlist Download Failed!</b>\n\nPlease check the logs for details.")
    else:
        logger.info("🎬 Detected single video URL")
        success = download_audio(url, output_dir)
        if not success:
            send_telegram_message("❌ <b>Download Failed!</b>\n\nPlease check the logs for details.")

if __name__ == '__main__':
    cli()
