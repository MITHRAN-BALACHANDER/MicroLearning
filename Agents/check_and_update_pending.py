"""
Check and update pending video generation jobs
"""
from agents.text_to_video_agent import TextToVideoAgent
from database.operations import SessionLocal
from database.models import VideoGenerationJob
from loguru import logger

def check_pending_jobs():
    """Check all pending jobs and update their status"""
    db = SessionLocal()
    agent = TextToVideoAgent()
    
    try:
        # Get all pending jobs
        pending_jobs = db.query(VideoGenerationJob).filter(
            VideoGenerationJob.status == 'pending'
        ).all()
        
        logger.info(f"Found {len(pending_jobs)} pending jobs")
        
        for job in pending_jobs:
            logger.info(f"\nChecking Job {job.id}:")
            logger.info(f"  Task ID: {job.task_id}")
            logger.info(f"  Prompt: {job.prompt[:50]}...")
            logger.info(f"  Created: {job.created_at}")
            
            # Check status
            result = agent.check_task_status(job.task_id)
            
            if result["success"]:
                data = result["data"]
                status = data.get("status")
                video_url = data.get("video_url")
                
                logger.info(f"  API Status: {status}")
                if video_url:
                    logger.info(f"  Video URL: {video_url}")
                
                # Update database
                if status == "finished":
                    job.status = "completed"
                    job.video_url = video_url
                    logger.success(f"  ✅ Job {job.id} completed!")
                elif status == "failed":
                    job.status = "failed"
                    job.error_message = "Video generation failed"
                    logger.error(f"  ❌ Job {job.id} failed")
                elif status == "processing":
                    logger.info(f"  ⏳ Job {job.id} still processing")
                else:
                    logger.warning(f"  ⚠️ Unknown status: {status}")
                
                db.commit()
            else:
                logger.error(f"  ❌ Failed to check status: {result.get('error')}")
        
        logger.info("\n" + "="*50)
        logger.info("Status check complete!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_pending_jobs()
