"""
Script to sync videos from MongoDB to the local application
Fetches videos, adds them to the database, and generates questions
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
from pymongo import MongoClient
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import add_video, get_db, init_db
from database.models import Video, Question
from agents.question_agent import QuestionAgent
from config.settings import GEMINI_API_KEY
import google.generativeai as genai


class MongoDBVideoSyncer:
    """Sync videos from MongoDB to local database"""
    
    def __init__(self, mongodb_uri: str):
        """
        Initialize the syncer
        
        Args:
            mongodb_uri: MongoDB connection URI
        """
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            
            # Try to get database name from URI or use default
            try:
                db_name = self.client.get_default_database().name
            except:
                # If no default database, list all databases and use the first non-system one
                db_list = self.client.list_database_names()
                logger.info(f"Available databases: {db_list}")
                
                # Filter out system databases
                user_dbs = [db for db in db_list if db not in ['admin', 'local', 'config']]
                
                if user_dbs:
                    db_name = user_dbs[0]
                    logger.info(f"Using database: {db_name}")
                else:
                    # Use default name if no user databases found
                    db_name = 'test'
                    logger.warning(f"No user databases found, using default: {db_name}")
            
            self.db = self.client[db_name]
            logger.info(f"Connected to MongoDB database: {db_name}")
            
            # List collections
            collections = self.db.list_collection_names()
            logger.info(f"Available collections: {collections}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            return False
    
    def fetch_videos(self) -> List[Dict[str, Any]]:
        """
        Fetch all videos from MongoDB
        
        Returns:
            List of video documents
        """
        try:
            # Try common collection names
            possible_collections = ['videos', 'video', 'content', 'media']
            videos = []
            
            for collection_name in possible_collections:
                if collection_name in self.db.list_collection_names():
                    logger.info(f"Found collection: {collection_name}")
                    collection = self.db[collection_name]
                    docs = list(collection.find())
                    logger.info(f"Found {len(docs)} documents in {collection_name}")
                    videos.extend(docs)
            
            # If no videos found in standard collections, check all collections
            if not videos:
                for collection_name in self.db.list_collection_names():
                    collection = self.db[collection_name]
                    docs = list(collection.find())
                    if docs:
                        logger.info(f"Checking collection: {collection_name} ({len(docs)} docs)")
                        # Print sample document structure
                        if len(docs) > 0:
                            logger.info(f"Sample document from {collection_name}: {list(docs[0].keys())}")
                        videos.extend(docs)
            
            logger.info(f"Total videos fetched: {len(videos)}")
            return videos
            
        except Exception as e:
            logger.error(f"Error fetching videos: {str(e)}")
            return []
    
    def map_video_fields(self, mongo_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map MongoDB document fields to local video schema
        
        Args:
            mongo_doc: MongoDB document
            
        Returns:
            Mapped video data
        """
        # Common field mappings
        field_mappings = {
            'title': ['title', 'name', 'video_title', 'videoTitle', 'filename'],
            'description': ['description', 'desc', 'summary', 'details', 'info'],
            'file_id': ['file_id', 'fileId', 'video_id', 'videoId', 'id', '_id'],
            'file_path': ['file_path', 'filePath', 'url', 'video_url', 'videoUrl', 'path'],
            'duration': ['duration', 'length', 'time', 'video_duration'],
            'transcript': ['transcript', 'subtitles', 'captions', 'text'],
            'category': ['category', 'type', 'genre', 'topic', 'subject'],
            'difficulty_level': ['difficulty', 'level', 'difficulty_level']
        }
        
        mapped_data = {}
        
        # Map each field
        for target_field, source_fields in field_mappings.items():
            value = None
            for source_field in source_fields:
                if source_field in mongo_doc:
                    value = mongo_doc[source_field]
                    break
            
            # Convert _id to string if needed
            if target_field == 'file_id' and value and hasattr(value, '__str__'):
                value = str(value)
            
            mapped_data[target_field] = value
        
        # Set defaults for required fields
        if not mapped_data.get('title'):
            mapped_data['title'] = f"Video_{mongo_doc.get('_id', 'unknown')}"
        
        if not mapped_data.get('file_id'):
            mapped_data['file_id'] = str(mongo_doc.get('_id', f"mongo_{datetime.now().timestamp()}"))
        
        if not mapped_data.get('description'):
            mapped_data['description'] = "Video synced from MongoDB"
        
        if not mapped_data.get('category'):
            mapped_data['category'] = 'general'
        
        if not mapped_data.get('difficulty_level'):
            mapped_data['difficulty_level'] = 1
        
        return mapped_data
    
    def check_video_exists(self, file_id: str) -> bool:
        """
        Check if video already exists in local database
        
        Args:
            file_id: Video file ID
            
        Returns:
            True if exists, False otherwise
        """
        with get_db() as db:
            video = db.query(Video).filter(Video.file_id == file_id).first()
            return video is not None
    
    async def generate_questions_for_video(self, video_id: int, video_data: Dict[str, Any], num_questions: int = 5) -> List[Dict]:
        """
        Generate questions for a video using AI
        
        Args:
            video_id: Local video ID
            video_data: Video metadata
            num_questions: Number of questions to generate
            
        Returns:
            List of generated questions
        """
        try:
            prompt = f"""
            Based on this video content, generate {num_questions} conceptual questions that test understanding:
            
            Title: {video_data.get('title', 'Unknown')}
            Description: {video_data.get('description', 'No description')}
            Category: {video_data.get('category', 'general')}
            Difficulty Level: {video_data.get('difficulty_level', 1)}
            
            Generate questions that:
            1. Test conceptual understanding, not memorization
            2. Are open-ended and require explanation
            3. Cover different aspects of the content
            4. Are appropriate for the difficulty level
            5. Are practical and applicable to real-world scenarios
            
            Return as JSON array with format:
            [
                {{
                    "question": "Clear, specific question text",
                    "concepts_tested": ["concept1", "concept2"],
                    "difficulty": 1-5,
                    "question_type": "open"
                }}
            ]
            
            IMPORTANT: Return ONLY valid JSON array, no additional text or markdown.
            """
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={'temperature': 0.7}
            )
            
            content = response.text.strip()
            
            # Clean up response
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            questions_data = json.loads(content)
            
            # Handle if the response is wrapped in a key
            if isinstance(questions_data, dict):
                questions_data = questions_data.get('questions', [])
            
            # Save questions to database
            saved_questions = []
            with get_db() as db:
                for q_data in questions_data[:num_questions]:
                    question = Question(
                        video_id=video_id,
                        question_text=q_data.get('question', ''),
                        question_type=q_data.get('question_type', 'open'),
                        concepts_tested=json.dumps(q_data.get('concepts_tested', [])),
                        difficulty=q_data.get('difficulty', 1),
                        is_active=True
                    )
                    db.add(question)
                    saved_questions.append(q_data)
                
                db.commit()
            
            logger.info(f"Generated {len(saved_questions)} questions for video {video_id}")
            return saved_questions
            
        except Exception as e:
            logger.error(f"Error generating questions for video {video_id}: {str(e)}")
            return []
    
    async def sync_videos(self, generate_questions: bool = True, num_questions: int = 5):
        """
        Main sync function - fetch videos and add to local database
        
        Args:
            generate_questions: Whether to generate questions for videos
            num_questions: Number of questions to generate per video
        """
        if not self.connect():
            logger.error("Failed to connect to MongoDB")
            return
        
        try:
            # Ensure database is initialized
            init_db()
            logger.info("Database initialized")
            
            # Fetch videos from MongoDB
            mongo_videos = self.fetch_videos()
            
            if not mongo_videos:
                logger.warning("No videos found in MongoDB")
                return
            
            added_count = 0
            skipped_count = 0
            error_count = 0
            
            logger.info(f"Processing {len(mongo_videos)} videos...")
            
            for idx, mongo_doc in enumerate(mongo_videos, 1):
                try:
                    # Map fields
                    video_data = self.map_video_fields(mongo_doc)
                    
                    # Check if already exists
                    if self.check_video_exists(video_data['file_id']):
                        logger.info(f"[{idx}/{len(mongo_videos)}] Video already exists: {video_data['title']}")
                        skipped_count += 1
                        continue
                    
                    # Add to database
                    with get_db() as db:
                        video = Video(
                            title=video_data['title'],
                            description=video_data['description'],
                            file_id=video_data['file_id'],
                            file_path=video_data.get('file_path'),
                            duration=video_data.get('duration'),
                            transcript=video_data.get('transcript'),
                            category=video_data.get('category', 'general'),
                            difficulty_level=video_data.get('difficulty_level', 1),
                            order_index=added_count,
                            is_active=True
                        )
                        db.add(video)
                        db.commit()
                        db.refresh(video)
                        
                        logger.info(f"[{idx}/{len(mongo_videos)}] Added video: {video.title} (ID: {video.id})")
                        added_count += 1
                        
                        # Generate questions if requested
                        if generate_questions:
                            logger.info(f"Generating {num_questions} questions for video {video.id}...")
                            questions = await self.generate_questions_for_video(
                                video.id,
                                video_data,
                                num_questions=num_questions
                            )
                            logger.info(f"Generated {len(questions)} questions")
                
                except Exception as e:
                    logger.error(f"[{idx}/{len(mongo_videos)}] Error processing video: {str(e)}")
                    error_count += 1
                    continue
            
            # Print summary
            logger.info("\n" + "="*60)
            logger.info("SYNC SUMMARY")
            logger.info("="*60)
            logger.info(f"Total videos processed: {len(mongo_videos)}")
            logger.info(f"Videos added: {added_count}")
            logger.info(f"Videos skipped (already exist): {skipped_count}")
            logger.info(f"Errors: {error_count}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error during sync: {str(e)}")
        finally:
            if self.client:
                self.client.close()
                logger.info("MongoDB connection closed")


async def main():
    """Main entry point"""
    # MongoDB URI
    MONGODB_URI = "mongodb+srv://jsajith76_db_user:Winter_bear_07@cluster0.4nftcbi.mongodb.net/?appName=Cluster0"
    
    logger.info("Starting MongoDB video sync...")
    logger.info(f"MongoDB URI: {MONGODB_URI[:50]}...")
    
    syncer = MongoDBVideoSyncer(MONGODB_URI)
    
    # Sync videos and generate questions
    await syncer.sync_videos(
        generate_questions=True,
        num_questions=5  # Generate 5 questions per video
    )
    
    logger.info("Sync completed!")


if __name__ == "__main__":
    asyncio.run(main())
