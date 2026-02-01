"""
Generate questions for videos using Gemini text model
Since video upload API is not available, we'll generate questions based on:
- Video filename
- Video title
- Video description
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


class SimpleQuestionGenerator:
    """Generate questions for videos using text-based prompts"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        # Use gemini-pro model which is more widely available
        self.model = genai.GenerativeModel('gemini-2.5-flash-latest')
        logger.info("Initialized Question Generator with Gemini Pro")
    
    def generate_questions_from_title(
        self, 
        video_title: str,
        video_description: str,
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Generate questions based on video title and description
        
        Args:
            video_title: Title of the video
            video_description: Description of the video
            num_questions: Number of questions to generate
            
        Returns:
            Dict with questions and metadata
        """
        try:
            logger.info(f"Generating questions for: {video_title}")
            
            prompt = f"""
            Based on this educational video, generate {num_questions} thoughtful questions:
            
            Title: {video_title}
            Description: {video_description}
            
            Generate questions that:
            1. Test conceptual understanding of the topic
            2. Are open-ended and require explanation
            3. Cover different aspects of the subject
            4. Are appropriate for educational assessment
            5. Include a mix of difficulty levels
            
            Also provide:
            - A better formatted title (if needed)
            - A detailed summary/description (2-3 paragraphs)
            - Key concepts covered
            - Learning objectives
            - Appropriate category (general, technical, business, onboarding)
            - Difficulty level (1-5)
            
            Return as JSON with this exact format:
            {{
                "title": "Better formatted title",
                "summary": "Detailed 2-3 paragraph description",
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
                        "sample_answer": "Brief sample answer"
                    }}
                ]
            }}
            
            Return ONLY valid JSON, no markdown formatting.
            """
            
            response = self.model.generate_content(
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
            
            result = json.loads(content)
            
            logger.info(f"✅ Generated {len(result.get('questions', []))} questions")
            return result
            
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
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
        """Update video with improved metadata"""
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
                    logger.info(f"✅ Updated metadata for video {video_id}")
                    return True
        except Exception as e:
            logger.error(f"Error updating video metadata: {str(e)}")
            return False
    
    def process_all_videos(self, delay_seconds: int = 10):
        """
        Process all videos without questions
        
        Args:
            delay_seconds: Delay between API calls
        """
        logger.info("="*70)
        logger.info("QUESTION GENERATION FOR ALL VIDEOS")
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
                
                # Generate questions based on title and description
                result = self.generate_questions_from_title(
                    video.title,
                    video.description
                )
                
                if result and result.get('questions'):
                    # Update video metadata
                    self.update_video_metadata(video.id, result)
                    
                    # Save questions
                    if self.save_questions_to_db(video.id, result['questions']):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    logger.error("Failed to generate questions")
                
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
        logger.info(f"Successfully generated: {success_count}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Total questions generated: ~{success_count * 5}")
        logger.info("="*70)


def main():
    """Main entry point"""
    logger.info("Starting question generation for all videos...")
    logger.info("")
    
    # Check for API key
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found in environment!")
        return
    
    logger.info("Starting in 3 seconds... (Press Ctrl+C to cancel)")
    time.sleep(3)
    
    generator = SimpleQuestionGenerator()
    generator.process_all_videos(delay_seconds=10)
    
    logger.info("\nQuestion generation completed!")


if __name__ == "__main__":
    main()
