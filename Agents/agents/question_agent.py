"""
Question & Rating Agent - Asks questions and rates answers based on video content
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from loguru import logger
import google.generativeai as genai

from database.operations import (
    get_user_by_telegram_id,
    get_questions_for_video,
    add_question,
    save_quiz_attempt,
    get_db
)
from database.models import Video, VideoProgress
from config.settings import GEMINI_API_KEY, QUESTION_AGENT_PROMPT


class QuestionAgent:
    """
    Dynamic agent responsible for:
    - Generating questions from video content
    - Asking users conceptual questions
    - Rating and evaluating answers
    - Providing feedback
    """
    
    def __init__(self, telegram_bot):
        self.bot = telegram_bot
        self.name = "QuestionAgent"
        self.description = "Generates and evaluates quiz questions"
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.active_quizzes = {}  # telegram_id -> quiz_state
        logger.info(f"Initialized {self.name}")
    
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
                            "question": q.question_text,
                            "concepts": json.loads(q.concepts_tested) if q.concepts_tested else []
                        }
                        for q in existing_questions
                    ]
                
                # Generate new questions using AI
                prompt = f"""
                Based on this video content, generate {num_questions} conceptual questions that test understanding:
                
                Title: {video.title}
                Description: {video.description}
                Transcript: {video.transcript or "No transcript available"}
                Key Concepts: {video.concepts or "General concepts"}
                
                Generate questions that:
                1. Test conceptual understanding, not memorization
                2. Are open-ended and require explanation
                3. Cover different aspects of the content
                4. Are appropriate for the difficulty level
                
                Return as JSON array with format:
                [
                    {{
                        "question": "question text",
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
                        question_text=q_data.get('question', ''),
                        concepts_tested=q_data.get('concepts_tested', []),
                        difficulty=q_data.get('difficulty', 1)
                    )
                    saved_questions.append({
                        "id": question.id,
                        "question": question.question_text,
                        "concepts": json.loads(question.concepts_tested) if question.concepts_tested else []
                    })
                
                logger.info(f"Generated {len(saved_questions)} questions for video {video_id}")
                return saved_questions
                
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return []
    
    async def start_quiz(self, telegram_id: str) -> Dict[str, Any]:
        """
        Start a quiz session for a user based on their last watched video
        
        Args:
            telegram_id: User's Telegram ID
            
        Returns:
            Dict with quiz status and first question
        """
        try:
            user = get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get last watched video
            with get_db() as db:
                last_progress = db.query(VideoProgress).filter(
                    VideoProgress.user_id == user.id
                ).order_by(VideoProgress.watched_at.desc()).first()
                
                if not last_progress:
                    return {
                        "success": False,
                        "error": "Please watch a video first using /video command"
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
            self.active_quizzes[telegram_id] = {
                "video_id": video_id,
                "questions": questions,
                "current_index": 0,
                "answers": [],
                "started_at": datetime.utcnow()
            }
            
            # Send first question
            first_question = questions[0]
            await self.bot.send_message(
                chat_id=telegram_id,
                text=f"📝 **Quiz Time!**\n\n"
                     f"Question 1/{len(questions)}:\n\n"
                     f"{first_question['question']}\n\n"
                     f"Please type your answer:"
            )
            
            return {
                "success": True,
                "message": "Quiz started",
                "total_questions": len(questions)
            }
            
        except Exception as e:
            logger.error(f"Error starting quiz: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def evaluate_answer(self, telegram_id: str, answer: str) -> Dict[str, Any]:
        """
        Evaluate a user's answer using AI and provide rating/feedback
        
        Args:
            telegram_id: User's Telegram ID
            answer: User's answer text
            
        Returns:
            Dict with evaluation results
        """
        try:
            if telegram_id not in self.active_quizzes:
                return {
                    "success": False,
                    "error": "No active quiz. Start one with /quiz"
                }
            
            quiz_state = self.active_quizzes[telegram_id]
            current_q = quiz_state["questions"][quiz_state["current_index"]]
            
            # Evaluate using AI
            eval_prompt = f"""
            Evaluate this answer to the question:
            
            Question: {current_q['question']}
            Concepts being tested: {', '.join(current_q.get('concepts', []))}
            User's Answer: {answer}
            
            Provide:
            1. A rating from 0-10 (10 being perfect understanding)
            2. Detailed feedback on what was correct/incorrect
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
            user = get_user_by_telegram_id(telegram_id)
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
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=f"✅ **Rating: {evaluation['rating']}/10**\n\n"
                         f"**Feedback:** {evaluation['feedback']}\n\n"
                         f"───────────\n\n"
                         f"Question {quiz_state['current_index'] + 1}/{len(quiz_state['questions'])}:\n\n"
                         f"{next_q['question']}\n\n"
                         f"Please type your answer:"
                )
                
                return {
                    "success": True,
                    "evaluation": evaluation,
                    "next_question": True
                }
            else:
                # Quiz completed
                avg_rating = sum(a["evaluation"]["rating"] for a in quiz_state["answers"]) / len(quiz_state["answers"])
                
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=f"✅ **Rating: {evaluation['rating']}/10**\n\n"
                         f"**Feedback:** {evaluation['feedback']}\n\n"
                         f"───────────\n\n"
                         f"🎉 **Quiz Completed!**\n\n"
                         f"Average Score: **{avg_rating:.1f}/10**\n\n"
                         f"Great job! Use /progress to see your overall progress."
                )
                
                # Clean up quiz state
                del self.active_quizzes[telegram_id]
                
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
