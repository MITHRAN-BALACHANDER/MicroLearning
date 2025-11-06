"""Check pending video generation jobs and their status."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.models import VideoGenerationJob, SessionLocal
from datetime import datetime

def check_pending_jobs():
    """Check all pending video generation jobs."""
    session = SessionLocal()
    
    try:
        # Get all pending jobs
        pending_jobs = session.query(VideoGenerationJob).filter_by(status='pending').all()
        
        print(f"\n{'='*80}")
        print(f"Found {len(pending_jobs)} pending video generation job(s)")
        print(f"{'='*80}\n")
        
        for job in pending_jobs:
            print(f"Job ID: {job.id}")
            print(f"Task ID: {job.task_id}")
            print(f"Prompt: {job.prompt}")
            print(f"Settings: {job.aspect_ratio}, {job.n_frames} frames")
            print(f"Created: {job.created_at}")
            
            # Calculate time elapsed
            elapsed = datetime.utcnow() - job.created_at
            minutes = elapsed.total_seconds() / 60
            print(f"Time Elapsed: {minutes:.1f} minutes")
            
            print(f"\n{'KIE.AI Task Check:':-^80}")
            print(f"Since KIE.AI doesn't provide a status API, you need to:")
            print(f"1. Visit: https://api.kie.ai/dashboard")
            print(f"2. Look for Task ID: {job.task_id}")
            print(f"3. Download the video if ready")
            print(f"4. Upload it to your system manually")
            print(f"{'='*80}\n")
        
        if len(pending_jobs) == 0:
            print("✅ No pending jobs found!")
            
    finally:
        session.close()

if __name__ == "__main__":
    check_pending_jobs()
