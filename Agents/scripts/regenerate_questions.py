"""
Regenerate quiz questions in the scenario-based format.

Questions are cached per video, so a video quizzed before scenarios existed
keeps serving its old questions forever. This retires those and builds new ones.

Old questions are deactivated rather than deleted: `quiz_attempts` reference
them, and a learner's past scores should keep pointing at the question they
actually answered.

    python scripts/regenerate_questions.py --status
    python scripts/regenerate_questions.py --video 3
    python scripts/regenerate_questions.py --all
"""
import argparse
import asyncio
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger  # noqa: E402

from database.models import Question, Video  # noqa: E402
from database.operations import get_db  # noqa: E402


def summarise() -> None:
    """Show which videos still have pre-scenario questions."""
    with get_db() as db:
        videos = db.query(Video).filter(Video.is_active == True).all()  # noqa: E712
        if not videos:
            print("No active videos.")
            return

        print(f"{'id':>4}  {'questions':>9}  {'scenarios':>9}  title")
        print("-" * 64)
        stale = 0
        for video in videos:
            questions = db.query(Question).filter(
                Question.video_id == video.id,
                Question.is_active == True,  # noqa: E712
            ).all()
            with_scenario = sum(1 for q in questions if q.scenario)
            if questions and not with_scenario:
                stale += 1
            print(f"{video.id:>4}  {len(questions):>9}  {with_scenario:>9}  {video.title[:38]}")

        print("-" * 64)
        print(f"{stale} video(s) still serving pre-scenario questions.")
        if stale:
            print("Run with --all to regenerate them.")


def retire(db, video_id: int) -> int:
    """
    Deactivate a video's questions so the agent generates fresh ones.

    Deactivated, not deleted: quiz_attempts point at these rows, and a
    learner's score history should still name the question they answered.
    """
    questions = db.query(Question).filter(
        Question.video_id == video_id,
        Question.is_active == True,  # noqa: E712
    ).all()
    for question in questions:
        question.is_active = False
    db.commit()
    return len(questions)


async def regenerate(video_ids, num_questions: int) -> None:
    from agents.question_agent import QuestionAgent

    # The agent only needs the router to *send* questions; generation does not
    # touch it, so a quiz can be rebuilt without a messaging client configured.
    agent = QuestionAgent.__new__(QuestionAgent)
    import google.generativeai as genai

    from config.settings import GEMINI_API_KEY

    genai.configure(api_key=GEMINI_API_KEY)
    agent.model = genai.GenerativeModel("gemini-2.5-flash")
    agent.router = None
    agent.active_quizzes = {}

    for video_id in video_ids:
        with get_db() as db:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                print(f"  video {video_id}: not found, skipped")
                continue
            title = video.title
            retired = retire(db, video_id)

        print(f"  video {video_id} ({title[:40]}): retired {retired}, generating...")
        questions = await agent.generate_questions_from_video(video_id, num_questions)

        if not questions:
            print(f"    FAILED - no questions generated; old ones stay retired")
            continue

        for index, question in enumerate(questions, 1):
            scenario = (question.get("scenario") or "").strip()
            print(f"    {index}. {'[scenario] ' if scenario else '[no scenario] '}"
                  f"{question['question'][:60]}")
            if scenario:
                print(f"       situation: {scenario[:70]}...")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true", help="show what is stale")
    group.add_argument("--all", action="store_true", help="regenerate every video")
    group.add_argument("--video", type=int, help="regenerate one video by id")
    parser.add_argument("--count", type=int, default=3, help="questions per video")
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="WARNING")

    if args.status:
        summarise()
        return

    if args.video:
        ids = [args.video]
    else:
        with get_db() as db:
            ids = [
                v.id for v in
                db.query(Video).filter(Video.is_active == True).all()  # noqa: E712
            ]

    if not ids:
        print("Nothing to regenerate.")
        return

    print(f"Regenerating questions for {len(ids)} video(s):")
    asyncio.run(regenerate(ids, args.count))
    print("\nDone. Run --status to confirm.")


if __name__ == "__main__":
    main()
