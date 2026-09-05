"""
One-off: add the CNC machining lesson (video + transcript + scenario quiz) to the DB.

    python scripts/add_cnc_video.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import init_db, add_video, add_question  # noqa: E402

VIDEO_PATH = str((Path(__file__).parent.parent / "data/videos/uploads/cnc_machining_basics.mp4").resolve())

TRANSCRIPT = """CNC stands for Computer Numerical Control.

It is a machine controlled by computer instructions to manufacture parts with high precision.

First, the CNC machine receives a programmed set of instructions called G-code.

These instructions tell the machine where and how the cutting tool should move.

Next, the raw material is securely fixed inside the machine.

The operator sets the required tools, coordinates, and work position before machining begins.

The machine controller moves the cutting tool precisely along the X, Y, and Z axes.

These controlled movements allow the machine to create complex shapes and dimensions.

As the tool moves according to the program, it removes material layer by layer.

This produces the required shape.

Finally, the finished part is inspected to verify its dimensions.

That is how CNC machining converts a digital program into a precise physical component."""

CONCEPTS = [
    "CNC (Computer Numerical Control)",
    "G-code",
    "workholding / fixturing",
    "tool, coordinate, and work position setup",
    "X, Y, Z axis movement",
    "material removal",
    "dimensional inspection",
]

QUESTIONS = [
    dict(
        scenario="A company needs to manufacture components with high precision using computer-controlled instructions.",
        question_text="What type of machine should be used?",
        correct_answer="A CNC machine.",
        concepts_tested=["CNC (Computer Numerical Control)"],
    ),
    dict(
        scenario="A CNC machine has received a programmed set of instructions that tells the cutting tool where and how to move.",
        question_text="What are these instructions called?",
        correct_answer="G-code.",
        concepts_tested=["G-code"],
    ),
    dict(
        scenario="An operator is ready to start machining, but the raw material is not securely fixed inside the machine.",
        question_text="What should the operator do?",
        correct_answer="Securely fix the raw material before machining begins.",
        concepts_tested=["workholding / fixturing"],
    ),
    dict(
        scenario="The raw material has been fixed, but the required tools, coordinates, and work position have not been set.",
        question_text="What should happen next?",
        correct_answer="The operator should set the required tools, coordinates, and work position before machining.",
        concepts_tested=["tool, coordinate, and work position setup"],
    ),
    dict(
        scenario="During machining, the cutting tool needs to move precisely in three directions.",
        question_text="Which axes control these movements?",
        correct_answer="X, Y, and Z axes.",
        concepts_tested=["X, Y, Z axis movement"],
    ),
    dict(
        scenario="A component requires complex shapes and precise dimensions.",
        question_text="How does the CNC machine achieve this?",
        correct_answer="By precisely controlling the cutting tool's movement along the X, Y, and Z axes according to the program.",
        concepts_tested=["X, Y, Z axis movement"],
    ),
    dict(
        scenario="A trainee observes that the CNC machine gradually removes material instead of producing the final shape in one step.",
        question_text="How is the material removed?",
        correct_answer="The tool removes material layer by layer according to the program.",
        concepts_tested=["material removal"],
    ),
    dict(
        scenario="The CNC machine has completed machining and produced the required shape.",
        question_text="What should happen before the component is considered complete?",
        correct_answer="The finished part should be inspected to verify its dimensions.",
        concepts_tested=["dimensional inspection"],
    ),
    dict(
        scenario="A trainee is asked to explain the complete CNC machining workflow.",
        question_text="What is the correct sequence?",
        correct_answer=(
            "Receive G-code -> Secure raw material -> Set tools, coordinates, and work position -> "
            "Control tool movement along X, Y, and Z axes -> Remove material layer by layer -> "
            "Produce the required shape -> Inspect the finished part."
        ),
        concepts_tested=["CNC (Computer Numerical Control)", "G-code", "dimensional inspection"],
    ),
    dict(
        scenario="A machine has the correct G-code and raw material, but the work position has not been configured.",
        question_text="Should machining begin?",
        correct_answer="No. The required tools, coordinates, and work position must be set before machining begins.",
        concepts_tested=["tool, coordinate, and work position setup"],
    ),
    dict(
        scenario="A trainee asks why CNC machining can produce complex shapes accurately.",
        question_text="What should they understand?",
        correct_answer="The machine controller precisely moves the cutting tool along the X, Y, and Z axes according to the programmed instructions.",
        concepts_tested=["X, Y, Z axis movement"],
    ),
    dict(
        scenario="A finished component looks correct, but its dimensions have not been checked.",
        question_text="What step has been missed?",
        correct_answer="Final inspection to verify the dimensions.",
        concepts_tested=["dimensional inspection"],
    ),
]


def main() -> None:
    if not os.path.exists(VIDEO_PATH):
        raise SystemExit(f"Video file not found: {VIDEO_PATH}")

    init_db()

    video = add_video(
        title="CNC Machining Basics",
        description="An introduction to CNC (Computer Numerical Control) machining: G-code, workholding, axis movement, and inspection.",
        file_id=VIDEO_PATH,
        file_path=VIDEO_PATH,
        transcript=TRANSCRIPT,
        concepts=CONCEPTS,
        difficulty_level=1,
    )
    print(f"Added video id={video.id}: {video.title}")

    for i, q in enumerate(QUESTIONS, 1):
        question = add_question(
            video_id=video.id,
            scenario=q["scenario"],
            question_text=q["question_text"],
            correct_answer=q["correct_answer"],
            concepts_tested=q["concepts_tested"],
            difficulty=1,
        )
        print(f"  [{i}] question id={question.id}: {question.question_text[:60]}")

    print(f"\nDone. Video {video.id} now has {len(QUESTIONS)} scenario-based questions.")


if __name__ == "__main__":
    main()
