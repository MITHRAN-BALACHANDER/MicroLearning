"""
Production-grade video processing utility for MicroLearning Admin Dashboard
Handles video clip uploads, concatenation, and final video generation
"""
import os
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import shutil

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
    from moviepy.video.fx import resize
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("moviepy not installed. Video processing features will be limited.")

from PIL import Image

# Configure logging
logger = logging.getLogger(__name__)

# Handle Pillow version compatibility - monkey patch for moviepy
try:
    # Pillow >= 10.0.0
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
    # Monkey patch ANTIALIAS for moviepy compatibility
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
except AttributeError:
    # Pillow < 10.0.0
    RESAMPLE_FILTER = Image.ANTIALIAS

class VideoProcessor:
    """
    Production-grade video processor for handling video clip uploads and compilation
    """
    
    ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB per clip
    MAX_TOTAL_DURATION = 3600  # 1 hour max total duration
    TARGET_RESOLUTION = (1920, 1080)  # Full HD
    TARGET_FPS = 30
    
    def __init__(self, upload_dir: str = "data/videos/uploads", output_dir: str = "data/videos/compiled"):
        """
        Initialize video processor
        
        Args:
            upload_dir: Directory for temporary clip uploads
            output_dir: Directory for final compiled videos
        """
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy is not available. Please install: pip install moviepy")
    
    def validate_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Validate uploaded video file
        
        Args:
            filepath: Path to the video file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(filepath)
        
        # Check if file exists
        if not path.exists():
            return False, "File does not exist"
        
        # Check extension
        if path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            return False, f"Invalid file format. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {self.MAX_FILE_SIZE / (1024*1024):.0f}MB"
        
        # Check if file is readable
        try:
            with open(filepath, 'rb') as f:
                f.read(1024)
        except Exception as e:
            return False, f"File is not readable: {str(e)}"
        
        return True, ""
    
    def get_video_info(self, filepath: str) -> Optional[Dict]:
        """
        Extract video metadata
        
        Args:
            filepath: Path to the video file
            
        Returns:
            Dictionary with video info or None if error
        """
        if not MOVIEPY_AVAILABLE:
            return None
        
        try:
            clip = VideoFileClip(filepath)
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': clip.size,
                'width': clip.w,
                'height': clip.h,
                'audio': clip.audio is not None
            }
            clip.close()
            return info
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    def save_uploaded_clip(self, file_stream, filename: str, session_id: str) -> Tuple[bool, str, str]:
        """
        Save uploaded video clip to temporary location
        
        Args:
            file_stream: File stream from upload
            filename: Original filename
            session_id: Unique session ID for this compilation
            
        Returns:
            Tuple of (success, filepath, error_message)
        """
        try:
            # Create session directory
            session_dir = self.upload_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            # Generate safe filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename}"
            filepath = session_dir / safe_filename
            
            # Save file
            file_stream.save(str(filepath))
            
            # Validate saved file
            is_valid, error_msg = self.validate_file(str(filepath))
            if not is_valid:
                filepath.unlink()  # Delete invalid file
                return False, "", error_msg
            
            logger.info(f"Saved clip: {filepath}")
            return True, str(filepath), ""
            
        except Exception as e:
            logger.error(f"Error saving clip: {e}")
            return False, "", str(e)
    
    def compile_clips(
        self,
        clip_paths: List[str],
        output_filename: str,
        title: Optional[str] = None,
        add_transitions: bool = True,
        normalize_audio: bool = True,
        target_resolution: Optional[Tuple[int, int]] = None
    ) -> Tuple[bool, str, str]:
        """
        Compile multiple video clips into a single video
        
        Args:
            clip_paths: List of video clip file paths
            output_filename: Name for the output file
            title: Optional title to add at the beginning
            add_transitions: Whether to add fade transitions
            normalize_audio: Whether to normalize audio levels
            target_resolution: Target resolution (width, height)
            
        Returns:
            Tuple of (success, output_path, error_message)
        """
        if not MOVIEPY_AVAILABLE:
            return False, "", "MoviePy not available. Please install: pip install moviepy"
        
        if not clip_paths:
            return False, "", "No clips provided"
        
        clips = []
        temp_files = []
        
        try:
            # Load and process all clips
            total_duration = 0
            resolution = target_resolution or self.TARGET_RESOLUTION
            
            for i, clip_path in enumerate(clip_paths):
                logger.info(f"Processing clip {i+1}/{len(clip_paths)}: {clip_path}")
                
                # Validate clip
                is_valid, error = self.validate_file(clip_path)
                if not is_valid:
                    raise ValueError(f"Invalid clip {clip_path}: {error}")
                
                # Load clip
                clip = VideoFileClip(clip_path)
                
                # Check total duration
                total_duration += clip.duration
                if total_duration > self.MAX_TOTAL_DURATION:
                    raise ValueError(f"Total duration exceeds maximum of {self.MAX_TOTAL_DURATION}s")
                
                # Resize to target resolution if needed
                if clip.size != resolution:
                    clip = clip.resize(resolution)
                
                # Set FPS
                if clip.fps != self.TARGET_FPS:
                    clip = clip.set_fps(self.TARGET_FPS)
                
                # Normalize audio if requested
                if normalize_audio and clip.audio is not None:
                    clip = clip.audio_normalize()
                
                clips.append(clip)
            
            # Add title screen if provided
            if title:
                title_clip = self._create_title_screen(title, duration=3, resolution=resolution)
                clips.insert(0, title_clip)
            
            # Add transitions if requested
            if add_transitions and len(clips) > 1:
                clips = self._add_fade_transitions(clips)
            
            # Concatenate all clips
            logger.info(f"Concatenating {len(clips)} clips...")
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Generate output path
            output_path = self.output_dir / output_filename
            if not output_filename.endswith('.mp4'):
                output_path = self.output_dir / f"{output_filename}.mp4"
            
            # Write final video
            logger.info(f"Writing final video to {output_path}...")
            final_clip.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=self.TARGET_FPS,
                preset='medium',
                threads=4,
                logger=None  # Suppress moviepy logs
            )
            
            # Clean up
            for clip in clips:
                clip.close()
            final_clip.close()
            
            logger.info(f"Successfully compiled video: {output_path}")
            return True, str(output_path), ""
            
        except Exception as e:
            logger.error(f"Error compiling clips: {e}")
            # Clean up clips
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            return False, "", str(e)
    
    def _create_title_screen(self, title: str, duration: float = 3, resolution: Tuple[int, int] = (1920, 1080)) -> VideoFileClip:
        """Create a title screen clip"""
        try:
            # Create text clip
            txt_clip = TextClip(
                title,
                fontsize=70,
                color='white',
                font='Arial-Bold',
                size=resolution,
                method='caption',
                align='center'
            )
            txt_clip = txt_clip.set_duration(duration)
            
            # Create black background
            from moviepy.video.VideoClip import ColorClip
            bg_clip = ColorClip(size=resolution, color=(0, 0, 0), duration=duration)
            
            # Composite
            final = CompositeVideoClip([bg_clip, txt_clip.set_position('center')])
            return final
        except Exception as e:
            logger.error(f"Error creating title screen: {e}")
            # Return simple black clip as fallback
            from moviepy.video.VideoClip import ColorClip
            return ColorClip(size=resolution, color=(0, 0, 0), duration=duration)
    
    def _add_fade_transitions(self, clips: List[VideoFileClip], fade_duration: float = 0.5) -> List[VideoFileClip]:
        """Add fade transitions between clips"""
        try:
            from moviepy.video.fx.fadein import fadein
            from moviepy.video.fx.fadeout import fadeout
            
            processed_clips = []
            for i, clip in enumerate(clips):
                # Add fade out to all clips except last
                if i < len(clips) - 1:
                    clip = clip.fx(fadeout, fade_duration)
                
                # Add fade in to all clips except first
                if i > 0:
                    clip = clip.fx(fadein, fade_duration)
                
                processed_clips.append(clip)
            
            return processed_clips
        except Exception as e:
            logger.error(f"Error adding transitions: {e}")
            return clips  # Return original clips if transitions fail
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up temporary files for a session
        
        Args:
            session_id: Session ID to clean up
            
        Returns:
            Success status
        """
        try:
            session_dir = self.upload_dir / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
                logger.info(f"Cleaned up session: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
            return False
    
    def get_session_clips(self, session_id: str) -> List[Dict]:
        """
        Get list of clips in a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of clip info dictionaries
        """
        session_dir = self.upload_dir / session_id
        if not session_dir.exists():
            return []
        
        clips = []
        for filepath in sorted(session_dir.glob("*")):
            if filepath.suffix.lower() in self.ALLOWED_EXTENSIONS:
                info = self.get_video_info(str(filepath))
                if info:
                    clips.append({
                        'filename': filepath.name,
                        'path': str(filepath),
                        'size': filepath.stat().st_size,
                        'duration': info['duration'],
                        'resolution': f"{info['width']}x{info['height']}"
                    })
        
        return clips
    
    def generate_thumbnail(self, video_path: str, time: float = 1.0) -> Optional[str]:
        """
        Generate thumbnail from video
        
        Args:
            video_path: Path to video file
            time: Time in seconds to extract frame
            
        Returns:
            Path to thumbnail image or None
        """
        if not MOVIEPY_AVAILABLE:
            return None
        
        try:
            clip = VideoFileClip(video_path)
            frame = clip.get_frame(min(time, clip.duration - 0.1))
            clip.close()
            
            # Save thumbnail
            thumbnail_path = Path(video_path).with_suffix('.jpg')
            img = Image.fromarray(frame)
            img.thumbnail((320, 180), RESAMPLE_FILTER)
            img.save(str(thumbnail_path), 'JPEG', quality=85)
            
            return str(thumbnail_path)
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None
