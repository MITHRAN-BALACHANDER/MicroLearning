"""
Script to remove all existing questions and regenerate them by analyzing videos
This script will:
1. Delete all existing questions from the database
2. Find all videos in the videos folder
3. Analyze each video using Gemini's video analysis
4. Generate questions based on video content
"""
import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import get_db
from database.models import Video, Question
from config.settings import GEMINI_API_KEY, VIDEOS_DIR
import google.generativeai as genai


class VideoQuestionGenerator:
    """Regenerate all questions by analyzing videos"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.videos_dir = Path(VIDEOS_DIR)
        logger.info("Initialized Video Question Generator with Gemini 2.0 Flash")
    
    def find_all_video_files(self) -> List[Path]:
        """Find all video files in the videos directory"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
        video_files = []
        
        logger.info(f"Scanning for videos in: {self.videos_dir}")
        
        # Search in all subdirectories
        for ext in video_extensions:
            video_files.extend(self.videos_dir.rglob(f"*{ext}"))
        
        logger.info(f"Found {len(video_files)} video files")
        return video_files
    
    async def analyze_video_and_generate_questions(
        self, 
        video_path: Path, 
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze a video file and generate questions
        
        Args:
            video_path: Path to video file
            num_questions: Number of questions to generate
            
        Returns:
            Dict with video analysis and questions
        """
        try:
            logger.info(f"Uploading and analyzing video: {video_path.name}")
            
            # Upload video file to Gemini
            video_file = await asyncio.to_thread(
                genai.upload_file,
                path=str(video_path)
            )
            
            logger.info(f"Video uploaded successfully. File URI: {video_file.uri}")
            
            # Wait for video processing
            logger.info("Waiting for video processing...")
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(2)
                video_file = await asyncio.to_thread(genai.get_file, video_file.name)
            
            if video_file.state.name == "FAILED":
                raise ValueError(f"Video processing failed: {video_file.state.name}")
            
            logger.info("Video processing complete. Generating analysis and questions...")
            
            # Generate comprehensive analysis and questions
            prompt = f"""
            Analyze this video comprehensively and provide:
            
            1. A detailed summary of the video content (2-3 paragraphs)
            2. Key concepts and topics covered
            3. Main learning objectives
            4. {num_questions} high-quality questions that test understanding
            
            The questions should:
            - Test conceptual understanding, not just memorization
            - Be open-ended and require thoughtful answers
            - Cover different aspects of the video content
            - Be appropriate for educational assessment
            - Include a mix of difficulty levels
            
            Return as JSON with this exact format:
            {{
                "title": "Suggested title based on video content",
                "summary": "Detailed summary of video content",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "learning_objectives": ["objective1", "objective2"],
                "category": "general|technical|business|onboarding",
                "difficulty_level": 1-5,
                "duration_estimate": estimated_duration_in_seconds,
                "questions": [
                    {{
                        "question": "Clear, specific question text",
                        "concepts_tested": ["concept1", "concept2"],
                        "difficulty": 1-5,
                        "question_type": "open",
                        "sample_answer": "Brief sample answer for reference"
                    }}
                ]
            }}
            
            IMPORTANT: Return ONLY valid JSON, no additional text or markdown formatting.
            """
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                [video_file, prompt],
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
            
            analysis = json.loads(content)
            
            # Add video file path
            analysis['video_path'] = str(video_path)
            analysis['video_filename'] = video_path.name
            
            logger.info(f"✅ Successfully analyzed video and generated {len(analysis.get('questions', []))} questions")
            
            # Clean up uploaded file
            try:
                await asyncio.to_thread(genai.delete_file, video_file.name)
                logger.info("Cleaned up uploaded video file from Gemini")
            except Exception as e:
                logger.warning(f"Could not delete uploaded file: {e}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing video {video_path.name}: {str(e)}")
            return None
    
    async def delete_all_questions(self):
        """Delete all existing questions from the database"""
        logger.info("Deleting all existing questions...")
        
        with get_db() as db:
            deleted_count = db.query(Question).delete()
            db.commit()
            logger.info(f"✅ Deleted {deleted_count} existing questions")
    
    async def update_or_create_video_in_db(self, analysis: Dict[str, Any]) -> Video:
        """Update existing video or create new one based on analysis"""
        with get_db() as db:
            video_path = analysis['video_path']
            
            # Try to find existing video by file_path
            video = db.query(Video).filter(Video.file_path == video_path).first()
            
            if video:
                # Update existing video
                logger.info(f"Updating existing video: {video.title}")
                video.title = analysis.get('title', video.title)
                video.description = analysis.get('summary', video.description)
                video.concepts = json.dumps(analysis.get('key_concepts', []))
                video.category = analysis.get('category', 'general')
                video.difficulty_level = analysis.get('difficulty_level', 1)
                video.duration = analysis.get('duration_estimate')
                video.is_active = True
            else:
                # Create new video
                logger.info(f"Creating new video: {analysis.get('title', 'Untitled')}")
                video = Video(
                    title=analysis.get('title', f"Video: {analysis['video_filename']}"),
                    description=analysis.get('summary', 'No description available'),
                    file_id=video_path,  # Using file_path as file_id for now
                    file_path=video_path,
                    concepts=json.dumps(analysis.get('key_concepts', [])),
                    category=analysis.get('category', 'general'),
                    difficulty_level=analysis.get('difficulty_level', 1),
                    duration=analysis.get('duration_estimate'),
                    is_active=True
                )
                db.add(video)
            
            db.commit()
            db.refresh(video)
            return video
    
    async def save_questions_to_db(self, video: Video, questions_data: List[Dict]):
        """Save generated questions to database"""
        with get_db() as db:
            for q_data in questions_data:
                question = Question(
                    video_id=video.id,
                    question_text=q_data.get('question', ''),
                    question_type=q_data.get('question_type', 'open'),
                    correct_answer=q_data.get('sample_answer'),
                    concepts_tested=json.dumps(q_data.get('concepts_tested', [])),
                    difficulty=q_data.get('difficulty', 1),
                    is_active=True
                )
                db.add(question)
            
            db.commit()
            logger.info(f"✅ Saved {len(questions_data)} questions for video {video.id}")
    
    async def regenerate_all_questions(self, delay_seconds: int = 15):
        """
        Main function to regenerate all questions
        
        Args:
            delay_seconds: Delay between API calls to avoid rate limits
        """
        logger.info("="*70)
        logger.info("STARTING COMPLETE QUESTION REGENERATION")
        logger.info("="*70)
        
        # Step 1: Delete all existing questions
        await self.delete_all_questions()
        
        # Step 2: Find all video files
        video_files = self.find_all_video_files()
        
        if not video_files:
            logger.warning("No video files found in the videos directory!")
            return
        
        logger.info(f"\nFound {len(video_files)} video files to process")
        logger.info("="*70)
        
        # Step 3: Process each video
        success_count = 0
        error_count = 0
        
        for idx, video_path in enumerate(video_files, 1):
            try:
                logger.info(f"\n[{idx}/{len(video_files)}] Processing: {video_path.name}")
                logger.info("-"*70)
                
                # Analyze video and generate questions
                analysis = await self.analyze_video_and_generate_questions(video_path)
                
                if analysis and analysis.get('questions'):
                    # Update or create video in database
                    video = await self.update_or_create_video_in_db(analysis)
                    
                    # Save questions to database
                    await self.save_questions_to_db(video, analysis['questions'])
                    
                    success_count += 1
                    logger.info(f"✅ Successfully processed video {idx}/{len(video_files)}")
                else:
                    error_count += 1
                    logger.error(f"❌ Failed to analyze video: {video_path.name}")
                
                # Delay to avoid rate limits (except for last video)
                if idx < len(video_files):
                    logger.info(f"Waiting {delay_seconds} seconds before next video...")
                    await asyncio.sleep(delay_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error processing video {video_path.name}: {str(e)}")
                error_count += 1
                continue
        
        # Print final summary
        logger.info("\n" + "="*70)
        logger.info("QUESTION REGENERATION COMPLETE")
        logger.info("="*70)
        logger.info(f"Videos found: {len(video_files)}")
        logger.info(f"Successfully processed: {success_count}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Total questions generated: ~{success_count * 5}")
        logger.info("="*70)


async def main():
    """Main entry point"""
    logger.info("Starting complete question regeneration process...")
    logger.info("This will:")
    logger.info("  1. Delete ALL existing questions")
    logger.info("  2. Analyze ALL videos in the videos folder")
    logger.info("  3. Generate NEW questions based on video analysis")
    logger.info("")
    
    # Wait 3 seconds to allow user to cancel if needed
    logger.info("Starting in 3 seconds... (Press Ctrl+C to cancel)")
    await asyncio.sleep(3)
    
    generator = VideoQuestionGenerator()
    
    # Process with 15-second delay between videos
    await generator.regenerate_all_questions(delay_seconds=15)
    
    logger.info("\nQuestion regeneration completed!")


if __name__ == "__main__":
    asyncio.run(main())
