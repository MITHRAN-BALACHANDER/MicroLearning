"""
Script to download videos from MongoDB and save them locally
Downloads videos from checked_videos collection and updates local database
"""
import os
import sys
import requests
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from pymongo import MongoClient
import hashlib
from urllib.parse import urlparse
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import get_db, init_db
from database.models import Video


class VideoDownloader:
    """Download videos from MongoDB and store locally"""
    
    def __init__(self, mongodb_uri: str, local_video_dir: str):
        """
        Initialize the downloader
        
        Args:
            mongodb_uri: MongoDB connection URI
            local_video_dir: Local directory to save videos
        """
        self.mongodb_uri = mongodb_uri
        self.local_video_dir = Path(local_video_dir)
        self.client = None
        self.db = None
        
        # Create video directory if it doesn't exist
        self.local_video_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Video directory: {self.local_video_dir}")
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            
            # Use the microlearning_db database (based on screenshot)
            db_name = 'microlearning_db'
            
            # Verify database exists
            db_list = self.client.list_database_names()
            logger.info(f"Available databases: {db_list}")
            
            if db_name not in db_list:
                logger.warning(f"Database '{db_name}' not found in available databases")
                logger.info("Trying alternative database names...")
                # Try other possible names
                for alt_name in ['microlearning', 'test', 'videos']:
                    if alt_name in db_list:
                        db_name = alt_name
                        logger.info(f"Using alternative database: {db_name}")
                        break
            
            self.db = self.client[db_name]
            logger.info(f"Connected to MongoDB database: {db_name}")
            
            # List collections
            collections = self.db.list_collection_names()
            logger.info(f"Available collections: {collections}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            return False
    
    def fetch_checked_videos(self) -> List[Dict[str, Any]]:
        """
        Fetch all videos from checked_videos collection
        
        Returns:
            List of video documents
        """
        try:
            collection = self.db['checked_videos']
            videos = list(collection.find())
            logger.info(f"Found {len(videos)} videos in checked_videos collection")
            return videos
        except Exception as e:
            logger.error(f"Error fetching videos: {str(e)}")
            return []
    
    def download_video(self, url: str, filename: str) -> bool:
        """
        Download a video from URL
        
        Args:
            url: Video URL
            filename: Local filename to save as
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = self.local_video_dir / filename
            
            # Skip if already downloaded
            if filepath.exists():
                logger.info(f"Video already exists: {filename}")
                return True
            
            logger.info(f"Downloading: {url}")
            
            # Download with streaming to handle large files
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Get total size if available
            total_size = int(response.headers.get('content-length', 0))
            
            # Download in chunks
            downloaded = 0
            chunk_size = 8192
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress for large files
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            if downloaded % (chunk_size * 100) == 0:  # Update every ~800KB
                                logger.info(f"Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")
            
            logger.info(f"✅ Downloaded: {filename} ({downloaded} bytes)")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to download {url}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Error downloading {url}: {str(e)}")
            return False
    
    def get_safe_filename(self, video_doc: Dict[str, Any]) -> str:
        """
        Generate a safe filename for the video
        
        Args:
            video_doc: MongoDB video document
            
        Returns:
            Safe filename
        """
        # Try to get title or use ID
        title = video_doc.get('title', '')
        video_id = str(video_doc.get('_id', ''))
        
        # Get file extension from URL
        video_url = video_doc.get('video_url', '')
        parsed = urlparse(video_url)
        ext = Path(parsed.path).suffix or '.mp4'
        
        # Create safe filename
        if title:
            # Clean title for filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            filename = f"{safe_title}_{video_id[:8]}{ext}"
        else:
            filename = f"video_{video_id}{ext}"
        
        return filename
    
    def update_local_database(self, video_doc: Dict[str, Any], local_path: str) -> bool:
        """
        Update local database with downloaded video path
        
        Args:
            video_doc: MongoDB video document
            local_path: Local file path
            
        Returns:
            True if successful
        """
        try:
            mongo_id = str(video_doc.get('_id'))
            
            with get_db() as db:
                # Find video by file_id (which we set to MongoDB _id during sync)
                video = db.query(Video).filter(Video.file_id == mongo_id).first()
                
                if video:
                    video.file_path = local_path
                    
                    # Update additional fields if available
                    if 'title' in video_doc and video_doc['title']:
                        video.title = video_doc['title']
                    if 'prompt' in video_doc:
                        video.description = video_doc['prompt']
                    
                    db.commit()
                    logger.info(f"✅ Updated database for video ID {video.id}")
                    return True
                else:
                    logger.warning(f"⚠️  Video not found in local database: {mongo_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating database: {str(e)}")
            return False
    
    def download_all_videos(self):
        """
        Main function to download all videos
        """
        if not self.connect():
            logger.error("Failed to connect to MongoDB")
            return
        
        try:
            # Ensure local database is initialized
            init_db()
            
            # Fetch videos from MongoDB
            mongo_videos = self.fetch_checked_videos()
            
            if not mongo_videos:
                logger.warning("No videos found in checked_videos collection")
                return
            
            success_count = 0
            fail_count = 0
            skip_count = 0
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting download of {len(mongo_videos)} videos...")
            logger.info(f"{'='*60}\n")
            
            for idx, video_doc in enumerate(mongo_videos, 1):
                try:
                    video_url = video_doc.get('video_url')
                    
                    if not video_url:
                        logger.warning(f"[{idx}/{len(mongo_videos)}] No video_url found, skipping")
                        skip_count += 1
                        continue
                    
                    # Generate safe filename
                    filename = self.get_safe_filename(video_doc)
                    local_path = str(self.local_video_dir / filename)
                    
                    logger.info(f"\n[{idx}/{len(mongo_videos)}] Processing: {video_doc.get('title', 'Untitled')}")
                    logger.info(f"URL: {video_url[:60]}...")
                    
                    # Check if already downloaded
                    if Path(local_path).exists():
                        logger.info(f"✅ Already downloaded: {filename}")
                        # Still update database
                        self.update_local_database(video_doc, local_path)
                        skip_count += 1
                        continue
                    
                    # Download video
                    if self.download_video(video_url, filename):
                        # Update local database
                        if self.update_local_database(video_doc, local_path):
                            success_count += 1
                        else:
                            logger.warning("Downloaded but failed to update database")
                            success_count += 1
                    else:
                        fail_count += 1
                    
                    # Small delay to be nice to the server
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"[{idx}/{len(mongo_videos)}] Error processing video: {str(e)}")
                    fail_count += 1
                    continue
            
            # Print summary
            logger.info(f"\n{'='*60}")
            logger.info("DOWNLOAD SUMMARY")
            logger.info(f"{'='*60}")
            logger.info(f"Total videos: {len(mongo_videos)}")
            logger.info(f"Successfully downloaded: {success_count}")
            logger.info(f"Skipped (already exist): {skip_count}")
            logger.info(f"Failed: {fail_count}")
            logger.info(f"Storage location: {self.local_video_dir.absolute()}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Error during download process: {str(e)}")
        finally:
            if self.client:
                self.client.close()
                logger.info("MongoDB connection closed")


def main():
    """Main entry point"""
    # MongoDB URI
    MONGODB_URI = "mongodb+srv://jsajith76_db_user:Winter_bear_07@cluster0.4nftcbi.mongodb.net/?appName=Cluster0"
    
    # Local video directory
    VIDEO_DIR = Path(__file__).parent.parent / "data" / "videos" / "uploads"
    
    logger.info("="*60)
    logger.info("VIDEO DOWNLOAD SCRIPT")
    logger.info("="*60)
    logger.info(f"MongoDB URI: {MONGODB_URI[:50]}...")
    logger.info(f"Local directory: {VIDEO_DIR}")
    logger.info("="*60)
    
    downloader = VideoDownloader(MONGODB_URI, str(VIDEO_DIR))
    downloader.download_all_videos()
    
    logger.info("\n✅ Download process completed!")


if __name__ == "__main__":
    main()
