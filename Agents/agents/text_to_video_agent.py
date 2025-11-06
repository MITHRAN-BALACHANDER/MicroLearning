"""
Text-to-Video Generation Agent using KIE.AI API
Handles video generation requests and tracks job status
"""
import requests
import json
import asyncio
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from database.operations import SessionLocal
from database.models import VideoGenerationJob, Video
from config.settings import KIE_API_KEY, KIE_API_URL


class TextToVideoAgent:
    """Agent for generating videos from text prompts using KIE.AI API"""
    
    def __init__(self):
        self.api_url = KIE_API_URL or "https://api.kie.ai/api/v1/jobs/createTask"
        self.api_key = KIE_API_KEY or "f9dbdbefa5beb4b61912891e4c88f6dd"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        logger.info("TextToVideoAgent initialized")
    
    def create_video_generation_task(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        n_frames: str = "30",
        remove_watermark: bool = True,
        callback_url: Optional[str] = None
    ) -> Dict:
        """
        Create a video generation task
        
        Args:
            prompt: Text description for the video
            aspect_ratio: Video aspect ratio (16:9, portrait, square)
            n_frames: Number of frames as string (10, 20, 30)
            remove_watermark: Whether to remove watermark
            callback_url: URL for callback when video is ready
            
        Returns:
            Dict with task information
        """
        try:
            # Map aspect ratios to KIE.AI API format
            aspect_ratio_map = {
                "16:9": "landscape",
                "portrait": "portrait",
                "square": "square",
                "9:16": "portrait",
                "1:1": "square"
            }
            api_aspect_ratio = aspect_ratio_map.get(aspect_ratio, "landscape")
            
            # Ensure n_frames is just a number string "10" or "15" (based on API docs)
            # The image shows "10s" and "15s" are UI labels for 10 and 15 seconds
            # But the API expects plain numbers
            n_frames_str = str(n_frames)
            
            payload = {
                "model": "sora-2-text-to-video",
                "callBackUrl": callback_url or "",
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": api_aspect_ratio,
                    "n_frames": n_frames_str,
                    "remove_watermark": remove_watermark
                }
            }
            
            logger.info(f"Creating video generation task for prompt: {prompt[:50]}...")
            logger.debug(f"API URL: {self.api_url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            # Log response for debugging
            logger.info(f"API Response Status: {response.status_code}")
            logger.debug(f"API Response Headers: {dict(response.headers)}")
            logger.debug(f"API Response Body: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Video generation task created successfully: {result}")
            return {
                "success": True,
                "data": result
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
            logger.error(f"HTTP Error creating video generation task: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": e.response.status_code
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating video generation task: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_task_status(self, task_id: str) -> Dict:
        """
        Check the status of a video generation task
        
        Args:
            task_id: The task ID returned from create_video_generation_task
            
        Returns:
            Dict with task status information
        """
        try:
            # Correct endpoint: queryTask (companion to createTask)
            status_url = f"https://api.kie.ai/api/v1/jobs/queryTask?taskId={task_id}"
            
            logger.info(f"Checking status for task: {task_id}")
            logger.debug(f"Status URL: {status_url}")
            
            # Try GET first
            response = requests.get(
                status_url,
                headers=self.headers,
                timeout=30
            )
            
            # If GET fails with 404, try POST with JSON body
            if response.status_code == 404:
                logger.debug("GET failed, trying POST with JSON body")
                response = requests.post(
                    "https://api.kie.ai/api/v1/jobs/queryTask",
                    headers=self.headers,
                    json={"taskId": task_id},
                    timeout=30
                )
            
            logger.debug(f"Status Response: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            # Parse the response
            # Expected format (from KIE.AI docs):
            # {
            #   "code": 200,
            #   "data": {
            #     "state": "success" | "fail" | "processing",
            #     "taskId": "xxxx",
            #     "resultJson": "{\"resultUrls\":[\"https://.../video.mp4\"]}"
            #   }
            # }
            
            if result.get("code") == 200:
                data = result.get("data", {})
                state = data.get("state", "unknown")
                task_id_response = data.get("taskId")
                result_json_str = data.get("resultJson", "{}")
                
                logger.info(f"Task {task_id} state: {state}")
                
                # Parse resultJson if available
                video_url = None
                if result_json_str and result_json_str != "{}":
                    try:
                        result_data = json.loads(result_json_str)
                        result_urls = result_data.get("resultUrls", [])
                        if result_urls:
                            video_url = result_urls[0]
                            logger.info(f"Video URL: {video_url}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse resultJson: {e}")
                
                # Map state to our status
                status_map = {
                    "success": "finished",
                    "fail": "failed",
                    "processing": "processing"
                }
                status = status_map.get(state, state)
                
                return {
                    "success": True,
                    "data": {
                        "status": status,
                        "state": state,
                        "video_url": video_url,
                        "task_id": task_id_response,
                        "raw_response": result
                    }
                }
            else:
                logger.warning(f"Unexpected response code: {result.get('code')}")
                return {
                    "success": False,
                    "error": result.get("msg", "Unknown error"),
                    "data": result
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking task status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_generation_job(
        self,
        prompt: str,
        task_id: str,
        user_id: Optional[int] = None,
        telegram_id: Optional[str] = None,
        aspect_ratio: str = "16:9",
        n_frames: str = "30"
    ) -> VideoGenerationJob:
        """
        Save video generation job to database
        
        Args:
            prompt: The text prompt used
            task_id: The task ID from KIE.AI
            user_id: User database ID
            telegram_id: Telegram user ID
            aspect_ratio: Video aspect ratio
            n_frames: Number of frames (string)
            
        Returns:
            VideoGenerationJob object
        """
        db = SessionLocal()
        try:
            job = VideoGenerationJob(
                prompt=prompt,
                task_id=task_id,
                user_id=user_id,
                telegram_id=telegram_id,
                status="pending",
                aspect_ratio=aspect_ratio,
                n_frames=str(n_frames)  # Ensure it's string
            )
            
            db.add(job)
            db.commit()
            db.refresh(job)
            
            logger.info(f"Saved generation job {job.id} for task {task_id}")
            return job
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving generation job: {str(e)}")
            raise
        finally:
            db.close()
    
    def update_job_status(
        self,
        job_id: int,
        status: str,
        video_url: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Update the status of a generation job
        
        Args:
            job_id: The job database ID
            status: New status (pending, processing, completed, failed)
            video_url: URL of the generated video
            error_message: Error message if failed
        """
        db = SessionLocal()
        try:
            job = db.query(VideoGenerationJob).filter(
                VideoGenerationJob.id == job_id
            ).first()
            
            if job:
                job.status = status
                if video_url:
                    job.video_url = video_url
                if error_message:
                    job.error_message = error_message
                
                if status == "completed":
                    job.completed_at = datetime.utcnow()
                
                db.commit()
                logger.info(f"Updated job {job_id} status to {status}")
            else:
                logger.warning(f"Job {job_id} not found")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating job status: {str(e)}")
        finally:
            db.close()
    
    async def generate_video_async(
        self,
        prompt: str,
        user_id: Optional[int] = None,
        telegram_id: Optional[str] = None,
        aspect_ratio: str = "16:9",
        n_frames: str = "30",
        callback_url: Optional[str] = None
    ) -> Dict:
        """
        Asynchronously generate a video
        
        Args:
            prompt: Text description for the video
            user_id: User database ID
            telegram_id: Telegram user ID
            aspect_ratio: Video aspect ratio
            n_frames: Number of frames (string)
            callback_url: URL for callback
            
        Returns:
            Dict with generation result
        """
        # Create generation task
        result = self.create_video_generation_task(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            n_frames=n_frames,
            callback_url=callback_url
        )
        
        if not result["success"]:
            return result
        
        # Extract task ID from response
        task_data = result["data"]
        task_id = task_data.get("taskId") or task_data.get("task_id") or task_data.get("id")
        
        if not task_id:
            logger.error("No task ID in response")
            return {
                "success": False,
                "error": "No task ID returned from API"
            }
        
        # Save to database
        try:
            job = self.save_generation_job(
                prompt=prompt,
                task_id=str(task_id),
                user_id=user_id,
                telegram_id=telegram_id,
                aspect_ratio=aspect_ratio,
                n_frames=n_frames
            )
            
            return {
                "success": True,
                "job_id": job.id,
                "task_id": task_id,
                "message": "Video generation started successfully",
                "data": task_data
            }
            
        except Exception as e:
            logger.error(f"Error saving job: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to save job: {str(e)}"
            }
    
    def get_user_generation_jobs(
        self,
        user_id: Optional[int] = None,
        telegram_id: Optional[str] = None
    ) -> list:
        """
        Get all generation jobs for a user
        
        Args:
            user_id: User database ID
            telegram_id: Telegram user ID
            
        Returns:
            List of VideoGenerationJob objects
        """
        db = SessionLocal()
        try:
            query = db.query(VideoGenerationJob)
            
            if user_id:
                query = query.filter(VideoGenerationJob.user_id == user_id)
            elif telegram_id:
                query = query.filter(VideoGenerationJob.telegram_id == telegram_id)
            
            jobs = query.order_by(VideoGenerationJob.created_at.desc()).all()
            return jobs
            
        finally:
            db.close()
    
    def download_generated_video(self, video_url: str, save_path: str) -> bool:
        """
        Download a generated video from URL
        
        Args:
            video_url: URL of the generated video
            save_path: Local path to save the video
            
        Returns:
            Boolean indicating success
        """
        try:
            logger.info(f"Downloading video from {video_url}")
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded successfully to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            return False
