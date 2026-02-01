"""
Simple and reliable question generator
Generates questions based on video titles and intelligently inferred content
With automatic quota handling and retry delays
"""
import os
import sys
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
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


class QuickQuestionGenerator:
    """Generate quality questions efficiently"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        # Use gemini-2.5-flash
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.max_retries = 3
        logger.info("Initialized Quick Question Generator")
    
    def extract_retry_delay(self, error_message: str) -> Optional[int]:
        """Extract retry delay from quota error message"""
        try:
            # Look for "Please retry in X.Xs" pattern
            match = re.search(r'Please retry in (\d+(?:\.\d+)?)s', error_message)
            if match:
                return int(float(match.group(1))) + 1  # Add 1 second buffer
        except:
            pass
        return None
    
    def is_quota_error(self, error_message: str) -> bool:
        """Check if error is a quota exceeded error"""
        return '429' in error_message or 'quota' in error_message.lower()
    
    def generate_comprehensive_questions(
        self, 
        video_title: str,
        video_description: str,
        num_questions: int = 5,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Generate comprehensive questions and metadata with retry logic"""
        try:
            logger.info(f"Generating questions for: {video_title}")
            
            prompt = f"""
            You are an expert educational content creator. Based on this video information, create high-quality educational content:
            
            Video Title: {video_title}
            Current Description: {video_description}
            
            Your task:
            1. Infer what the video is likely about based on the title
            2. Create a detailed, engaging description (2-3 paragraphs)
            3. Identify key concepts and learning objectives
            4. Generate {num_questions} thoughtful, educational questions
            
            Requirements for questions:
            - Test conceptual understanding and critical thinking
            - Be open-ended and require explanation
            - Cover different aspects of the topic
            - Range from basic (difficulty 1-2) to advanced (difficulty 4-5)
            - Be relevant and practical
            
            Return ONLY valid JSON (no markdown):
            {{
                "title": "Improved, descriptive title",
                "summary": "Engaging 2-3 paragraph description of what the video covers",
                "key_concepts": ["concept1", "concept2", "concept3", "concept4"],
                "learning_objectives": ["objective1", "objective2", "objective3"],
                "category": "general or technical or business or onboarding",
                "difficulty_level": 3,
                "questions": [
                    {{
                        "question": "Clear, specific question text",
                        "concepts_tested": ["concept1", "concept2"],
                        "difficulty": 3,
                        "question_type": "open",
                        "sample_answer": "Comprehensive sample answer"
                    }}
                ]
            }}
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.8,
                    'max_output_tokens': 4096
                }
            )
            
            content = response.text.strip()
            
            # Clean response
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Try to parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Content length: {len(content)}")
                logger.error(f"Start: {content[:200]}")
                logger.error(f"End: {content[-200:]}")
                raise
            
            logger.info(f"✅ Generated {len(result.get('questions', []))} questions")
            return result
            
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a quota error
            if self.is_quota_error(error_str):
                retry_delay = self.extract_retry_delay(error_str)
                
                if retry_delay and retry_count < self.max_retries:
                    logger.warning(f"⏳ Quota limit hit. Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    return self.generate_comprehensive_questions(
                        video_title, 
                        video_description, 
                        num_questions,
                        retry_count + 1
                    )
                else:
                    logger.error(f"❌ Quota exceeded. Please try again later or upgrade your API plan.")
                    logger.error(f"   Error: {error_str[:200]}")
                    return None
            
            logger.error(f"Error generating questions: {error_str}")
            if 'response' in locals():
                logger.error(f"Response: {response.text[:500]}")
            return None
    
    def save_questions_to_db(self, video_id: int, questions_data: List[Dict]):
        """Save questions to database"""
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
                logger.info(f"✅ Saved {len(questions_data)} questions")
                return True
        except Exception as e:
            logger.error(f"Error saving questions: {str(e)}")
            return False
    
    def update_video_metadata(self, video_id: int, analysis: Dict[str, Any]):
        """Update video metadata"""
        try:
            with get_db() as db:
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    if analysis.get('title'):
                        video.title = analysis['title']
                    if analysis.get('summary'):
                        video.description = analysis['summary']
                    if analysis.get('key_concepts'):
                        video.concepts = json.dumps(analysis['key_concepts'])
                    if analysis.get('category'):
                        video.category = analysis['category']
                    if analysis.get('difficulty_level'):
                        video.difficulty_level = analysis['difficulty_level']
                    
                    db.commit()
                    logger.info(f"✅ Updated metadata")
                    return True
        except Exception as e:
            logger.error(f"Error updating metadata: {str(e)}")
            return False
    
    def process_all_videos(self, delay_seconds: int = 10):
        """Process all videos without questions"""
        logger.info("="*70)
        logger.info("QUESTION GENERATION FOR ALL VIDEOS")
        logger.info("With automatic quota handling")
        logger.info("="*70)
        
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
            logger.info("✅ All videos already have questions!")
            return
        
        logger.info(f"Found {len(videos_to_process)} videos to process")
        logger.info("="*70)
        
        success_count = 0
        error_count = 0
        quota_hit = False
        
        for idx, video in enumerate(videos_to_process, 1):
            try:
                logger.info(f"\n[{idx}/{len(videos_to_process)}] {video.title}")
                logger.info("-"*70)
                
                result = self.generate_comprehensive_questions(
                    video.title,
                    video.description
                )
                
                if result and result.get('questions'):
                    self.update_video_metadata(video.id, result)
                    
                    if self.save_questions_to_db(video.id, result['questions']):
                        success_count += 1
                        logger.info(f"✅ Successfully processed {idx}/{len(videos_to_process)}")
                    else:
                        error_count += 1
                elif result is None:
                    # Check if we hit quota limit
                    error_count += 1
                    quota_hit = True
                    logger.warning(f"⚠️  Stopping due to quota limits. Progress saved.")
                    break
                else:
                    error_count += 1
                    logger.error("❌ Failed to generate questions")
                
                if idx < len(videos_to_process):
                    logger.info(f"Waiting {delay_seconds}s before next video...")
                    time.sleep(delay_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error: {str(e)}")
                error_count += 1
                continue
        
        logger.info("\n" + "="*70)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*70)
        logger.info(f"Total videos: {len(videos_to_process)}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {error_count}")
        logger.info(f"Remaining: {len(videos_to_process) - success_count - error_count}")
        logger.info(f"Questions generated: ~{success_count * 5}")
        
        if quota_hit:
            logger.info("")
            logger.info("⚠️  API QUOTA LIMIT REACHED")
            logger.info("Options:")
            logger.info("  1. Wait 24 hours and run again")
            logger.info("  2. Upgrade to paid API tier")
            logger.info("  3. Run script again to resume from where it stopped")
        
        logger.info("="*70)


def main():
    """Main entry point"""
    logger.info("Starting question generation with auto-retry...")
    logger.info("The script will automatically handle quota limits and retry delays")
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found!")
        return
    
    logger.info("\nStarting in 3 seconds... (Ctrl+C to cancel)")
    time.sleep(3)
    
    generator = QuickQuestionGenerator()
    generator.process_all_videos(delay_seconds=10)
    
    logger.info("\n✅ Script completed!")


if __name__ == "__main__":
    main()
