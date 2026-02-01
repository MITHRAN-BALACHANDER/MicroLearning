"""
Quick verification script to check synced videos and questions
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import get_db
from database.models import Video, Question


def verify_sync():
    """Verify the MongoDB sync results"""
    with get_db() as db:
        # Get all videos and questions
        videos = db.query(Video).all()
        questions = db.query(Question).all()
        
        # Calculate stats
        video_ids_with_questions = set([q.video_id for q in questions])
        videos_with_questions = len(video_ids_with_questions)
        videos_without_questions = len(videos) - videos_with_questions
        
        print("\n" + "="*60)
        print("DATABASE STATUS")
        print("="*60)
        print(f"Total Videos: {len(videos)}")
        print(f"Total Questions: {len(questions)}")
        print(f"Videos with Questions: {videos_with_questions}")
        print(f"Videos without Questions: {videos_without_questions}")
        
        if questions:
            avg_questions = len(questions) / videos_with_questions
            print(f"Average Questions per Video: {avg_questions:.1f}")
        
        print("\n" + "="*60)
        print("SAMPLE VIDEOS")
        print("="*60)
        for i, video in enumerate(videos[:10], 1):
            q_count = len([q for q in questions if q.video_id == video.id])
            status = "✅" if q_count > 0 else "⏳"
            print(f"{status} {i}. {video.title[:45]}... (ID: {video.id}, Questions: {q_count})")
        
        if len(videos) > 10:
            print(f"... and {len(videos) - 10} more videos")
        
        print("\n" + "="*60)
        print("CATEGORIES")
        print("="*60)
        categories = {}
        for video in videos:
            categories[video.category] = categories.get(video.category, 0) + 1
        
        for category, count in sorted(categories.items()):
            print(f"{category}: {count} videos")
        
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        if videos_without_questions > 0:
            print(f"⚠️  {videos_without_questions} videos need questions")
            print("Run: python scripts/generate_missing_questions.py")
            print("(After Gemini API quota resets)")
        else:
            print("✅ All videos have questions!")
        print("="*60 + "\n")


if __name__ == "__main__":
    verify_sync()
