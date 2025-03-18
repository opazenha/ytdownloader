#!/usr/bin/env python3
"""
Test script for the YouTube MP3 Downloader.
"""

import os
import sys
import logging
from youtube_mp3 import download_audio, download_playlist

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_single_video():
    """Test downloading a single video."""
    # A short, copyright-free video for testing (Big Buck Bunny trailer)
    test_url = "https://www.youtube.com/watch?v=YE7VzlLtp-4"
    output_dir = os.path.join(os.getcwd(), "test_downloads")
    
    print("Testing single video download...")
    try:
        success = download_audio(test_url, output_dir)
        
        if success:
            print("✅ Single video test passed!")
        else:
            print("❌ Single video test failed!")
    except Exception as e:
        print(f"❌ Single video test failed with exception: {str(e)}")

def test_playlist():
    """Test downloading a playlist."""
    # A short, copyright-free playlist for testing (Blender Foundation videos)
    test_playlist_url = "https://www.youtube.com/playlist?list=PLa1F2ddGya_-UvuAqHAksYnB0qL9yWDO6"
    output_dir = os.path.join(os.getcwd(), "test_downloads")
    
    print("Testing playlist download (with 5-second delay instead of 60 for testing)...")
    try:
        success = download_playlist(test_playlist_url, output_dir, delay=5)
        
        if success:
            print("✅ Playlist test passed!")
        else:
            print("❌ Playlist test failed!")
    except Exception as e:
        print(f"❌ Playlist test failed with exception: {str(e)}")

if __name__ == "__main__":
    # Create test directory
    os.makedirs(os.path.join(os.getcwd(), "test_downloads"), exist_ok=True)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--playlist":
        test_playlist()
    else:
        test_single_video()
