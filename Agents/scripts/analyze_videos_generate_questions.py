"""
Script to analyze videos and generate questions using Gemini API
This uses the Files API correctly for video analysis
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import get_db
from database.models import Video, Question
from config.settings import GEMINI_API_KEY
import google.generativeai as genai


class VideoAnalyzer:
    """Analyze videos and generate questions using Gemini"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        # Use gemini-1.5-flash for video analysis
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Initialized Video Analyzer with Gemini 1.5 Flash")
    
    def upload_video_file(self, video_path: str):
        """Upload video file to Gemini using Files API"""
        try:
            logger.info(f"Uploading video: {Path(video_path).name}")
            
            # Upload file using the Files API
            video_file = genai.upload_file(path=video_path)
            logger.info(f"Upload complete: {video_file.name}")
            
            # Wait for processing
            logger.info("Processing video...")
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                raise Exception(f"Video processing failed")
            
            logger.info("✅ Video processed successfully")
            return video_file
            
        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            return None
    
    def analyze_video_and_generate_questions(
        self, 
        video_file, 
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze uploaded video and generate questions
        
        Args:
            video_file: Uploaded Gemini file object
            num_questions: Number of questions to generate
            
        Returns:
            Dict with analysis and questions
        """
        try:
            logger.info("Analyzing video content and generating questions...")
            
            prompt = f"""
            Analyze this video comprehensively and provide:
            
            1. A detailed summary of the video content (2-3 paragraphs)
            2. Key concepts and topics covered
            3. Main learning objectives
            4. {num_questions} high-quality educational questions
            
            The questions should:
            - Test conceptual understanding, not just memorization
            - Be open-ended and require thoughtful answers
            - Cover different aspects of the video content
            - Be appropriate for educational assessment
            - Include a mix of difficulty levels (1-5)
            
            Return as JSON with this exact format:
            {{
                "summary": "Detailed 2-3 paragraph summary",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "learning_objectives": ["objective1", "objective2"],
                "category": "general",
                "difficulty_level": 3,
                "questions": [
                    {{
                        "question": "Clear, specific question text",
                        "concepts_tested": ["concept1", "concept2"],
                        "difficulty": 3,
                        "question_type": "open",
                        "sample_answer": "Brief sample answer for reference"
                    }}
                ]
            }}
            
            Return ONLY valid JSON, no markdown formatting.
            """
            
            response = self.model.generate_content(
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
            
            logger.info(f"✅ Analysis complete with {len(analysis.get('questions', []))} questions")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            return None
    
    def save_questions_to_db(self, video_id: int, questions_data: List[Dict]):
        """Save generated questions to database"""
        try:
            with get_db() as db:
                for q_data in questions_data:
                    question = Question(
                        video_id=video_id,
                        question_text=q_data.get('question', ''),
                        question_type=q_data.get('question_type', 'open'),
                        correct_answer=q_data.get('sample_answer'),
                        concepts_tested=json.dumps(q_data.get('concepts_tested', [])),
                        difficulty=q_data.get('difficulty', 1),
                        is_active=True
                    )
                    db.add(question)
                
                db.commit()
                logger.info(f"✅ Saved {len(questions_data)} questions for video {video_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving questions: {str(e)}")
            return False
    
    def update_video_metadata(self, video_id: int, analysis: Dict[str, Any]):
        """Update video with analysis metadata"""
        try:
            with get_db() as db:
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    if analysis.get('summary'):
                        video.description = analysis['summary']
                    if analysis.get('key_concepts'):
                        video.concepts = json.dumps(analysis['key_concepts'])
                    if analysis.get('category'):
                        video.category = analysis['category']
                    if analysis.get('difficulty_level'):
                        video.difficulty_level = analysis['difficulty_level']
                    
                    db.commit()
                    logger.info(f"✅ Updated metadata for video {video_id}")
                    return True
        except Exception as e:
            logger.error(f"Error updating video metadata: {str(e)}")
            return False
    
    def process_all_videos(self, delay_seconds: int = 15):
        """
        Process all videos without questions
        
        Args:
            delay_seconds: Delay between API calls
        """
        logger.info("="*70)
        logger.info("VIDEO ANALYSIS AND QUESTION GENERATION")
        logger.info("="*70)
        
        # Get videos without questions
        with get_db() as db:
            videos = db.query(Video).filter(Video.is_active == True).all()
            
            videos_to_process = []
            for video in videos:
                question_count = db.query(Question).filter(
                    Question.video_id == video.id,
                    Question.is_active == True
                ).count()
                
                if question_count == 0:
                    videos_to_process.append(video)
        
        if not videos_to_process:
            logger.info("All videos already have questions!")
            return
        
        logger.info(f"Found {len(videos_to_process)} videos without questions")
        logger.info("="*70)
        
        success_count = 0
        error_count = 0
        
        for idx, video in enumerate(videos_to_process, 1):
            try:
                logger.info(f"\n[{idx}/{len(videos_to_process)}] Processing: {video.title}")
                logger.info("-"*70)
                
                # Check if file exists
                if not os.path.exists(video.file_path):
                    logger.error(f"Video file not found: {video.file_path}")
                    error_count += 1
                    continue
                
                # Upload video
                video_file = self.upload_video_file(video.file_path)
                if not video_file:
                    error_count += 1
                    continue
                
                # Analyze and generate questions
                analysis = self.analyze_video_and_generate_questions(video_file)
                
                if analysis and analysis.get('questions'):
                    # Update video metadata
                    self.update_video_metadata(video.id, analysis)
                    
                    # Save questions
                    if self.save_questions_to_db(video.id, analysis['questions']):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    logger.error("Failed to generate questions")
                
                # Clean up uploaded file
                try:
                    genai.delete_file(video_file.name)
                    logger.info("Cleaned up uploaded file")
                except Exception as e:
                    logger.warning(f"Could not delete file: {e}")
                
                # Delay before next video
                if idx < len(videos_to_process):
                    logger.info(f"Waiting {delay_seconds} seconds...")
                    time.sleep(delay_seconds)
                
            except Exception as e:
                logger.error(f"Error processing video {video.title}: {str(e)}")
                error_count += 1
                continue
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("PROCESSING COMPLETE")
        logger.info("="*70)
        logger.info(f"Videos processed: {len(videos_to_process)}")
        logger.info(f"Successfully analyzed: {success_count}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Total questions generated: ~{success_count * 5}")
        logger.info("="*70)


def main():
    """Main entry point"""
    logger.info("Starting video analysis and question generation...")
    logger.info("")
    
    # Check for API key
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found in environment!")
        return
    
    logger.info("Starting in 3 seconds... (Press Ctrl+C to cancel)")
    time.sleep(3)
    
    analyzer = VideoAnalyzer()
    analyzer.process_all_videos(delay_seconds=15)
    
    logger.info("\nQuestion generation completed!")


if __name__ == "__main__":
    main()
