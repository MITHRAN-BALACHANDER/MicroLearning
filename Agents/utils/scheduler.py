"""
Scheduler utilities for periodic tasks
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from loguru import logger
from typing import Callable, Dict, Any


class TaskScheduler:
    """Manage scheduled tasks for the bot"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}
        logger.info("Initialized TaskScheduler")
    
    def add_daily_job(self, job_id: str, func: Callable, hour: int = 9, minute: int = 0):
        """
        Add a job that runs daily at specified time
        
        Args:
            job_id: Unique job identifier
            func: Function to execute
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        try:
            trigger = CronTrigger(hour=hour, minute=minute)
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                replace_existing=True
            )
            self.jobs[job_id] = job
            logger.info(f"Added daily job: {job_id} at {hour:02d}:{minute:02d}")
            
        except Exception as e:
            logger.error(f"Error adding daily job {job_id}: {str(e)}")
    
    def add_interval_job(self, job_id: str, func: Callable, minutes: int = 60):
        """
        Add a job that runs at regular intervals
        
        Args:
            job_id: Unique job identifier
            func: Function to execute
            minutes: Interval in minutes
        """
        try:
            job = self.scheduler.add_job(
                func,
                'interval',
                minutes=minutes,
                id=job_id,
                replace_existing=True
            )
            self.jobs[job_id] = job
            logger.info(f"Added interval job: {job_id} every {minutes} minutes")
            
        except Exception as e:
            logger.error(f"Error adding interval job {job_id}: {str(e)}")
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed job: {job_id}")
            
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def get_jobs(self) -> Dict[str, Any]:
        """Get all scheduled jobs"""
        return {
            job_id: {
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job_id, job in self.jobs.items()
        }
