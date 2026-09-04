"""
Question & Rating Agent - Asks questions and rates answers based on video content
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from loguru import logger

from database.operations import (
    get_user_by_ref,
    get_questions_for_video,
    add_question,
    save_quiz_attempt,
    get_db
)
from database.models import Video, VideoProgress
from messaging.formatting import DIVIDER, bold, italic, paragraphs, sanitize
from config.settings import GEMINI_API_KEY, QUESTION_AGENT_PROMPT
from messaging.base import UserRef


class QuestionAgent:
    """
    Dynamic agent responsible for:
    - Generating questions from video content
    - Asking users conceptual questions
    - Rating and evaluating answers
    - Providing feedback
    """

    def __init__(self, router):
        # Imported here so the module stays cheap to import for tests/tooling
        import google.generativeai as genai

        self.router = router
        self.name = "QuestionAgent"
        self.description = "Generates and evaluates quiz questions"
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        # Keyed by UserRef.key so a Telegram and a WhatsApp learner can never
        # collide even if their raw platform ids happen to match.
        self.active_quizzes = {}
        logger.info(f"Initialized {self.name}")

    def has_active_quiz(self, ref: UserRef) -> bool:
        return ref.key in self.active_quizzes
    
    # -- presentation -----------------------------------------------------
    # One place builds a question and one builds feedback, so every question in
    # a quiz looks the same and the two channels cannot drift.

    @staticmethod
    def _score_bar(rating: float) -> str:
        """
        A ten-block bar for the score.

        A bare "7/10" makes a learner do arithmetic to know how they did. The
        bar is read at a glance, which matters on a phone mid-shift.
        """
        filled = max(0, min(10, int(round(float(rating)))))
        return "●" * filled + "○" * (10 - filled)

    def _render_question(self, question: Dict[str, Any], index: int, total: int) -> str:
        """
        Render one question.

        The scenario is separated from the question by a labelled break so the
        learner can tell the situation from what is being asked of them - they
        arrive as one wall of text otherwise. Questions written before
        scenarios existed simply have no situation block.
        """
        parts = [bold(f"Question {index} of {total}")]

        scenario = (question.get("scenario") or "").strip()
        if scenario:
            parts.append(italic("The situation"))
            parts.append(sanitize(scenario))

        parts.append(bold(sanitize(question["question"])))
        parts.append(italic("Answer in a sentence or two - a voice note is fine."))
        return paragraphs(*parts)

    def _render_feedback(self, evaluation: Dict[str, Any]) -> str:
        """Render the score and feedback for one answer."""
        rating = evaluation.get("rating", 0)
        return paragraphs(
            bold(f"{rating}/10") + "  " + self._score_bar(rating),
            sanitize(evaluation.get("feedback", "")),
        )

    async def generate_questions_from_video(self, video_id: int, num_questions: int = 3) -> List[Dict[str, Any]]:
        """
        Generate conceptual questions from video content using AI
        
        Args:
            video_id: Video ID
            num_questions: Number of questions to generate
            
        Returns:
            List of generated questions
        """
        try:
            with get_db() as db:
                video = db.query(Video).filter(Video.id == video_id).first()
                if not video:
                    return []
                
                # Check if questions already exist
                existing_questions = get_questions_for_video(video_id)
                if existing_questions:
                    return [
                        {
                            "id": q.id,
                            "scenario": q.scenario or "",
                            "question": q.question_text,
                            "concepts": json.loads(q.concepts_tested) if q.concepts_tested else []
                        }
                        for q in existing_questions
                    ]
                
                # Generate new questions using AI.
                #
                # Scenario-based on purpose. "What are the three steps of the
                # returns process?" tests whether someone watched a video;
                # "A customer is at your counter with no receipt - what do you
                # do?" tests whether they could actually do the job. The second
                # is what the business cares about, and it is far harder to
                # answer by parroting the transcript back.
                prompt = f"""
                Write {num_questions} scenario-based questions from this lesson.

                Title: {video.title}
                Description: {video.description}
                Transcript: {video.transcript or "No transcript available"}
                Key Concepts: {video.concepts or "General concepts"}

                Each one is a short, realistic situation the learner could
                actually meet in their job, followed by a question about what
                they would do.

                Rules for the scenario:
                - 1 to 3 sentences, under 60 words. It is read on a phone.
                - Concrete and specific: a real moment, with a person in it.
                  Give people and places ordinary names.
                - It must be solvable using this lesson, and not solvable by
                  common sense alone.
                - Never state the answer inside the scenario.

                Rules for the question:
                - One sentence, asking what they would do or why.
                - Answerable in two or three spoken sentences - learners often
                  reply with a voice note.
                - Open-ended. Never yes/no, never multiple choice.

                Vary the situations across the {num_questions}: different
                people, different pressures, different parts of the lesson.

                Return as JSON array with format:
                [
                    {{
                        "scenario": "the situation, 1-3 sentences",
                        "question": "what would you do, and why?",
                        "concepts_tested": ["concept1", "concept2"],
                        "difficulty": 1-5
                    }}
                ]

                IMPORTANT: Return ONLY valid JSON, no additional text.
                """
                
                full_prompt = f"{QUESTION_AGENT_PROMPT}\n\n{prompt}"
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    generation_config={'temperature': 0.7}
                )
                
                content = response.text.strip()
                # Remove markdown code blocks if present
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                questions_data = json.loads(content)
                
                # Handle if the response is wrapped in a key
                if isinstance(questions_data, dict):
                    questions_data = questions_data.get('questions', [])
                
                # Save questions to database
                saved_questions = []
                for q_data in questions_data[:num_questions]:
                    question = add_question(
                        video_id=video_id,
                        scenario=q_data.get('scenario', '') or None,
                        question_text=q_data.get('question', ''),
                        concepts_tested=q_data.get('concepts_tested', []),
                        difficulty=q_data.get('difficulty', 1)
                    )
                    saved_questions.append({
                        "id": question.id,
                        "scenario": question.scenario or "",
                        "question": question.question_text,
                        "concepts": json.loads(question.concepts_tested) if question.concepts_tested else []
                    })
                
                logger.info(f"Generated {len(saved_questions)} questions for video {video_id}")
                return saved_questions
                
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return []
    
    async def start_quiz(self, ref: UserRef) -> Dict[str, Any]:
        """
        Start a quiz session for a user based on their last watched video

        Args:
            ref: UserRef identifying the learner and platform

        Returns:
            Dict with quiz status and first question
        """
        try:
            user = get_user_by_ref(ref)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get last watched video
            with get_db() as db:
                last_progress = db.query(VideoProgress).filter(
                    VideoProgress.user_id == user.id
                ).order_by(VideoProgress.watched_at.desc()).first()
                
                if not last_progress:
                    # Not a failure - the learner just has not started. The
                    # dispatcher turns this flag into an empty state with a
                    # "Watch first video" button.
                    return {
                        "success": False,
                        "needs_video": True,
                        "error": "No watched video to build a quiz from",
                    }
                
                video_id = last_progress.video_id
            
            # Generate or get questions
            questions = await self.generate_questions_from_video(video_id)
            if not questions:
                return {
                    "success": False,
                    "error": "Could not generate questions. Please try again."
                }
            
            # Initialize quiz session
            self.active_quizzes[ref.key] = {
                "video_id": video_id,
                "questions": questions,
                "current_index": 0,
                "answers": [],
                "started_at": datetime.utcnow()
            }

            # Send first question
            await self.router.send_message(
                ref, self._render_question(questions[0], 1, len(questions))
            )

            return {
                "success": True,
                "message": "Quiz started",
                "total_questions": len(questions)
            }
            
        except Exception as e:
            logger.error(f"Error starting quiz: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def evaluate_answer(self, ref: UserRef, answer: str) -> Dict[str, Any]:
        """
        Evaluate a user's answer using AI and provide rating/feedback

        Args:
            ref: UserRef identifying the learner and platform
            answer: User's answer text

        Returns:
            Dict with evaluation results
        """
        try:
            if ref.key not in self.active_quizzes:
                return {
                    "success": False,
                    "error": "No active quiz. Start one with /quiz"
                }

            quiz_state = self.active_quizzes[ref.key]
            current_q = quiz_state["questions"][quiz_state["current_index"]]
            
            # Evaluate using AI
            # The scenario is part of the question: "I'd check the receipt
            # first" can only be judged against the situation it answers.
            scenario = (current_q.get("scenario") or "").strip()
            scenario_block = f"Situation: {scenario}\n            " if scenario else ""

            eval_prompt = f"""
            Evaluate this answer to the question:

            {scenario_block}Question: {current_q['question']}
            Concepts being tested: {', '.join(current_q.get('concepts', []))}
            User's Answer: {answer}

            Judge whether they would handle the situation correctly, not
            whether they used the same words as the lesson. A learner who
            describes the right action in their own words is right. Mark down
            only for a wrong or unsafe action, or a missing step that matters.

            Write the feedback to the learner as "you", in at most three
            sentences: what they got right, then the single most useful thing
            they missed. No preamble, no restating the question.

            Provide:
            1. A rating from 0-10 (10 being perfect understanding)
            2. Feedback as described above
            3. Whether the answer demonstrates understanding (true/false)
            
            Return as JSON:
            {{
                "rating": 0-10,
                "feedback": "detailed feedback text",
                "demonstrates_understanding": true/false,
                "key_points_covered": ["point1", "point2"]
            }}
            
            IMPORTANT: Return ONLY valid JSON, no additional text.
            """
            
            full_prompt = f"{QUESTION_AGENT_PROMPT}\n\n{eval_prompt}"
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config={'temperature': 0.3}
            )
            
            content = response.text.strip()
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            evaluation = json.loads(content)
            
            # Save quiz attempt
            user = get_user_by_ref(ref)
            save_quiz_attempt(
                user_id=user.id,
                question_id=current_q["id"],
                user_answer=answer,
                rating=evaluation.get("rating", 0),
                feedback=evaluation.get("feedback", ""),
                is_correct=evaluation.get("demonstrates_understanding", False)
            )
            
            # Store answer
            quiz_state["answers"].append({
                "question": current_q["question"],
                "answer": answer,
                "evaluation": evaluation
            })
            
            # Move to next question or end quiz
            quiz_state["current_index"] += 1
            
            if quiz_state["current_index"] < len(quiz_state["questions"]):
                # Send next question
                next_q = quiz_state["questions"][quiz_state["current_index"]]
                # Two messages, not one. Feedback on the last answer and the
                # next scenario are different things to read; glued together
                # the learner skims the feedback to reach the question.
                await self.router.send_message(ref, self._render_feedback(evaluation))
                await self.router.send_message(
                    ref,
                    self._render_question(
                        next_q,
                        quiz_state["current_index"] + 1,
                        len(quiz_state["questions"]),
                    ),
                )

                return {
                    "success": True,
                    "evaluation": evaluation,
                    "next_question": True
                }
            else:
                # Quiz completed
                avg_rating = sum(a["evaluation"]["rating"] for a in quiz_state["answers"]) / len(quiz_state["answers"])
                
                answered = len(quiz_state["answers"])
                await self.router.send_message(ref, self._render_feedback(evaluation))
                await self.router.send_message(
                    ref,
                    paragraphs(
                        bold("Quiz complete"),
                        f"{bold(f'{avg_rating:.1f}/10')}  {self._score_bar(avg_rating)}",
                        f"Averaged across {answered} question"
                        f"{'s' if answered != 1 else ''}.",
                    ),
                )

                # Clean up quiz state
                del self.active_quizzes[ref.key]

                return {
                    "success": True,
                    "evaluation": evaluation,
                    "quiz_completed": True,
                    "average_rating": avg_rating
                }
                
        except Exception as e:
            logger.error(f"Error evaluating answer: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return {
            "name": self.name,
            "active_quizzes": len(self.active_quizzes),
            "status": "active"
        }
