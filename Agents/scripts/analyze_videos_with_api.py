"""
Analyze videos and generate questions using Gemini REST API
Direct API calls to upload and analyze video files
"""
import os
import sys
import json
import time
import requests
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


class VideoAnalyzerWithAPI:
    """Analyze video content using Gemini REST API"""
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        logger.info("Initialized Video Analyzer with Gemini REST API")
    
    def upload_video_file(self, video_path: str):
        """Upload video file using Files API"""
        try:
            logger.info(f"Uploading video: {Path(video_path).name}")
            
            # Upload endpoint
            upload_url = f"{self.base_url}/files?key={self.api_key}"
            
            # Get file metadata
            file_name = Path(video_path).name
            file_size = os.path.getsize(video_path)
            logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
            
            # Read video file
            with open(video_path, 'rb') as f:
                files = {
                    'file': (file_name, f, 'video/mp4')
                }
                headers = {
                    'X-Goog-Upload-Protocol': 'multipart'
                }
                
                response = requests.post(upload_url, files=files, headers=headers)
                
            if response.status_code != 200:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return None
            
            file_data = response.json()
            logger.debug(f"Upload response: {file_data}")
            
            # Parse response correctly - file data is at root level
            file_uri = file_data.get('uri') or file_data.get('file', {}).get('uri')
            file_name_api = file_data.get('name') or file_data.get('file', {}).get('name')
            
            if not file_name_api:
                logger.error(f"Failed to get file name from response: {file_data}")
                return None
            
            logger.info(f"✅ Upload complete: {file_name_api}")
            
            # Wait for processing
            logger.info("Waiting for video processing...")
            max_wait = 120  # 2 minutes max
            wait_time = 0
            
            while wait_time < max_wait:
                if not file_name_api:
                    logger.error("No file name available for status check")
                    return None
                    
                check_url = f"{self.base_url}/{file_name_api}?key={self.api_key}"
                check_response = requests.get(check_url)
                
                if check_response.status_code == 200:
                    file_status = check_response.json()
                    state = file_status.get('state', 'PROCESSING')
                    
                    if state == 'ACTIVE':
                        logger.info("✅ Video processed successfully")
                        return {
                            'uri': file_uri,
                            'name': file_name_api
                        }
                    elif state == 'FAILED':
                        logger.error("Video processing failed")
                        return None
                    
                    logger.info(f"Processing... (state: {state})")
                
                time.sleep(5)
                wait_time += 5
            
            logger.error("Video processing timeout")
            return None
            
        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            return None
    
    def analyze_video(self, file_uri: str, num_questions: int = 5):
        """Analyze video and generate questions"""
        try:
            logger.info("Analyzing video content...")
            
            prompt = f"""
            Watch and analyze this entire video carefully. Then provide:
            
            1. A comprehensive summary of what happens in the video (2-3 paragraphs)
            2. Key concepts, topics, or lessons covered
            3. Main learning objectives or takeaways
            4. {num_questions} high-quality educational questions based on the ACTUAL video content
            
            The questions MUST:
            - Be based on what you SEE and HEAR in the video
            - Test understanding of the video's actual content
            - Be open-ended and require thoughtful answers
            - Cover different aspects shown in the video
            - Range in difficulty from easy to challenging (1-5)
            
            Also provide:
            - A descriptive title based on the video content
            - Appropriate category (general, technical, business, onboarding)
            - Overall difficulty level (1-5)
            
            Return as JSON with this exact format:
            {{
                "title": "Descriptive title based on video content",
                "summary": "Detailed 2-3 paragraph summary of what's in the video",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "learning_objectives": ["objective1", "objective2"],
                "category": "general",
                "difficulty_level": 3,
                "questions": [
                    {{
                        "question": "Question about actual video content",
                        "concepts_tested": ["concept1", "concept2"],
                        "difficulty": 3,
                        "question_type": "open",
                        "sample_answer": "Answer based on video content"
                    }}
                ]
            }}
            
            IMPORTANT: Base everything on the ACTUAL video content.
            Return ONLY valid JSON, no markdown.
            """
            
            # Generate content endpoint
            model_url = f"{self.base_url}/models/gemini-1.5-pro-latest:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"fileData": {"fileUri": file_uri}},
                        {"text": prompt}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }
            
            response = requests.post(model_url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Analysis failed: {response.status_code} - {response.text}")
                return None
            
            result_data = response.json()
            
            # Extract text from response
            candidates = result_data.get('candidates', [])
            if not candidates:
                logger.error("No candidates in response")
                return None
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                logger.error("No parts in response")
                return None
            
            text = parts[0].get('text', '')
            
            # Clean up response
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]
            elif text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            analysis = json.loads(text)
            
            logger.info(f"✅ Video analyzed successfully")
            logger.info(f"   Generated {len(analysis.get('questions', []))} questions")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            return None
    
    def delete_file(self, file_name: str):
        """Delete uploaded file"""
        try:
            delete_url = f"{self.base_url}/{file_name}?key={self.api_key}"
            response = requests.delete(delete_url)
            if response.status_code == 200:
                logger.info("Cleaned up uploaded file")
        except Exception as e:
            logger.warning(f"Could not delete file: {e}")
    
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
                logger.info(f"✅ Saved {len(questions_data)} questions to database")
                return True
        except Exception as e:
            logger.error(f"Error saving questions: {str(e)}")
            return False
    
    def update_video_metadata(self, video_id: int, analysis: Dict[str, Any]):
        """Update video with analysis-based metadata"""
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
                    logger.info(f"✅ Updated video metadata")
                    return True
        except Exception as e:
            logger.error(f"Error updating video metadata: {str(e)}")
            return False
    
    def process_all_videos(self, delay_seconds: int = 25):
        """Process all videos without questions"""
        logger.info("="*70)
        logger.info("VIDEO CONTENT ANALYSIS FOR QUESTION GENERATION")
        logger.info("Analyzing actual video content using Gemini API")
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
            file_name = None
            try:
                logger.info(f"\n[{idx}/{len(videos_to_process)}] Processing: {video.title}")
                logger.info("-"*70)
                
                # Check if file exists
                if not os.path.exists(video.file_path):
                    logger.error(f"Video file not found: {video.file_path}")
                    error_count += 1
                    continue
                
                # Upload video
                file_data = self.upload_video_file(video.file_path)
                if not file_data:
                    error_count += 1
                    continue
                
                file_uri = file_data['uri']
                file_name = file_data['name']
                
                # Analyze video
                analysis = self.analyze_video(file_uri)
                
                if analysis and analysis.get('questions'):
                    # Update metadata
                    self.update_video_metadata(video.id, analysis)
                    
                    # Save questions
                    if self.save_questions_to_db(video.id, analysis['questions']):
                        success_count += 1
                        logger.info(f"✅ Successfully processed video {idx}/{len(videos_to_process)}")
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    logger.error("Failed to analyze video")
                
                # Cleanup
                if file_name:
                    self.delete_file(file_name)
                
                # Delay
                if idx < len(videos_to_process):
                    logger.info(f"Waiting {delay_seconds} seconds...")
                    time.sleep(delay_seconds)
                
            except Exception as e:
                logger.error(f"Error processing video: {str(e)}")
                error_count += 1
                if file_name:
                    self.delete_file(file_name)
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
    logger.info("Starting VIDEO CONTENT ANALYSIS...")
    logger.info("This analyzes actual video content, not just titles!")
    logger.info("")
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found!")
        return
    
    logger.info("Starting in 3 seconds... (Press Ctrl+C to cancel)")
    time.sleep(3)
    
    analyzer = VideoAnalyzerWithAPI()
    analyzer.process_all_videos(delay_seconds=25)
    
    logger.info("\nVideo analysis completed!")


if __name__ == "__main__":
    main()
