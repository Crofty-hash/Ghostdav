"""
Video Stream - Real-time webcam capture and streaming
WebRTC-compatible video streaming for video communication
"""

import cv2
import threading
import time
from typing import Optional, Callable, Dict, Any, Tuple
from dataclasses import dataclass
import logging
import queue
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VideoConfig:
    """Video stream configuration"""
    width: int = 640
    height: int = 480
    fps: int = 30
    device_index: int = 0
    codec: str = 'MJPEG'  # MJPEG, YUYV, etc.
    brightness: int = 50
    contrast: int = 50
    saturation: int = 50


@dataclass
class VideoFrame:
    """Video frame data"""
    data: np.ndarray
    timestamp: float
    sequence_number: int
    config: VideoConfig
    encoded_data: Optional[bytes] = None  # For compressed frames


class VideoStream:
    """Real-time video capture and streaming"""
    
    def __init__(self, config: Optional[VideoConfig] = None):
        """
        Initialize video stream
        
        Args:
            config: Video configuration
        """
        self.config = config or VideoConfig()
        self.capture = None
        self.is_streaming = False
        self.is_capturing = False
        
        # Threading
        self.capture_thread = None
        self.process_thread = None
        
        # Queues
        self.frame_queue = queue.Queue(maxsize=30)  # Buffer up to 30 frames
        
        # Callbacks
        self.frame_callback: Optional[Callable[[VideoFrame], None]] = None
        self.error_callback: Optional[Callable[[Exception], None]] = None
        
        # Sequence tracking
        self.frame_sequence = 0
        
        # Video processing
        self.motion_detection = False
        self.motion_threshold = 25
        self.last_frame = None
        
        # Encoding
        self.encode_frames = False
        self.codec = cv2.VideoWriter_fourcc(*'MJPG')
        
        logger.info(f"Video stream initialized: {self.config.width}x{self.config.height}@{self.config.fps}fps")
    
    def start_capture(self) -> bool:
        """
        Start video capture from webcam
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.capture is not None:
                self.stop_capture()
            
            self.capture = cv2.VideoCapture(self.config.device_index)
            
            if not self.capture.isOpened():
                raise Exception(f"Could not open camera {self.config.device_index}")
            
            # Configure camera
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.config.fps)
            self.capture.set(cv2.CAP_PROP_BRIGHTNESS, self.config.brightness)
            self.capture.set(cv2.CAP_PROP_CONTRAST, self.config.contrast)
            self.capture.set(cv2.CAP_PROP_SATURATION, self.config.saturation)
            
            # Verify settings
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            
            logger.info(f"Camera opened: {actual_width}x{actual_height}@{actual_fps}fps")
            
            self.is_capturing = True
            self.is_streaming = True
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            # Start processing thread
            self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.process_thread.start()
            
            logger.info("Video capture started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start video capture: {e}")
            if self.error_callback:
                self.error_callback(e)
            return False
    
    def stop_capture(self) -> None:
        """Stop video capture"""
        self.is_capturing = False
        self.is_streaming = False
        
        if self.capture:
            self.capture.release()
            self.capture = None
        
        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=1.0)
        
        # Clear queues
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("Video capture stopped")
    
    def pause_stream(self) -> None:
        """Pause video streaming (keep capture running)"""
        self.is_streaming = False
        logger.info("Video streaming paused")
    
    def resume_stream(self) -> None:
        """Resume video streaming"""
        self.is_streaming = True
        logger.info("Video streaming resumed")
    
    def set_frame_callback(self, callback: Callable[[VideoFrame], None]) -> None:
        """
        Set callback for video frames
        
        Args:
            callback: Function to call with each VideoFrame
        """
        self.frame_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """
        Set callback for errors
        
        Args:
            callback: Function to call on errors
        """
        self.error_callback = callback
    
    def enable_motion_detection(self, threshold: int = 25) -> None:
        """
        Enable motion detection
        
        Args:
            threshold: Motion detection threshold
        """
        self.motion_detection = True
        self.motion_threshold = threshold
        logger.info(f"Motion detection enabled with threshold {threshold}")
    
    def disable_motion_detection(self) -> None:
        """Disable motion detection"""
        self.motion_detection = False
        self.last_frame = None
        logger.info("Motion detection disabled")
    
    def enable_encoding(self, codec: str = 'MJPG') -> None:
        """
        Enable frame encoding
        
        Args:
            codec: Video codec ('MJPG', 'XVID', etc.)
        """
        self.encode_frames = True
        self.codec = cv2.VideoWriter_fourcc(*codec)
        logger.info(f"Frame encoding enabled with codec {codec}")
    
    def disable_encoding(self) -> None:
        """Disable frame encoding"""
        self.encode_frames = False
        logger.info("Frame encoding disabled")
    
    def get_video_devices(self) -> Dict[int, Dict[str, Any]]:
        """
        Get list of available video devices
        
        Returns:
            Dictionary of device index -> device info
        """
        devices = {}
        for i in range(10):  # Check first 10 indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                devices[i] = {
                    'name': f'Camera {i}',
                    'width': width,
                    'height': height,
                    'fps': fps
                }
                cap.release()
        return devices
    
    def _capture_loop(self) -> None:
        """Main video capture loop"""
        try:
            while self.is_capturing:
                if self.capture and self.capture.isOpened():
                    ret, frame = self.capture.read()
                    
                    if ret:
                        # Put frame in queue (non-blocking)
                        try:
                            self.frame_queue.put(frame, timeout=0.1)
                        except queue.Full:
                            # Drop oldest frame if queue is full
                            try:
                                self.frame_queue.get_nowait()
                                self.frame_queue.put(frame, timeout=0.1)
                            except queue.Empty:
                                pass
                    else:
                        logger.warning("Failed to read frame from camera")
                        time.sleep(0.1)
                else:
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Video capture error: {e}")
            if self.error_callback:
                self.error_callback(e)
    
    def _process_loop(self) -> None:
        """Video processing and frame generation loop"""
        try:
            while self.is_capturing:
                try:
                    # Get frame from queue
                    frame = self.frame_queue.get(timeout=0.1)
                    
                    # Process frame
                    if self._should_process_frame(frame):
                        video_frame = self._create_frame(frame)
                        
                        # Call callback if streaming
                        if self.is_streaming and self.frame_callback:
                            self.frame_callback(video_frame)
                    
                except queue.Empty:
                    continue
                    
        except Exception as e:
            logger.error(f"Video processing error: {e}")
            if self.error_callback:
                self.error_callback(e)
    
    def _should_process_frame(self, frame: np.ndarray) -> bool:
        """
        Determine if frame should be processed (motion detection)
        
        Args:
            frame: Video frame
        
        Returns:
            True if should process, False otherwise
        """
        if not self.motion_detection:
            return True
        
        # Convert to grayscale for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.last_frame is None:
            self.last_frame = gray
            return True
        
        # Calculate frame difference
        frame_delta = cv2.absdiff(self.last_frame, gray)
        thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = len(contours) > 0
        self.last_frame = gray
        
        return motion_detected
    
    def _create_frame(self, frame: np.ndarray) -> VideoFrame:
        """
        Create VideoFrame from raw frame data
        
        Args:
            frame: Raw video frame
        
        Returns:
            VideoFrame object
        """
        self.frame_sequence += 1
        
        # Encode frame if enabled
        encoded_data = None
        if self.encode_frames:
            encoded_data = self._encode_frame(frame)
        
        return VideoFrame(
            data=frame,
            timestamp=time.time(),
            sequence_number=self.frame_sequence,
            config=self.config,
            encoded_data=encoded_data
        )
    
    def _encode_frame(self, frame: np.ndarray) -> bytes:
        """
        Encode frame using configured codec
        
        Args:
            frame: Video frame
        
        Returns:
            Encoded frame data
        """
        try:
            # Create temporary video writer for single frame
            temp_file = f"/tmp/frame_{self.frame_sequence}.avi"
            writer = cv2.VideoWriter(temp_file, self.codec, 1, (frame.shape[1], frame.shape[0]))
            writer.write(frame)
            writer.release()
            
            # Read encoded data
            with open(temp_file, 'rb') as f:
                data = f.read()
            
            # Clean up
            import os
            os.remove(temp_file)
            
            return data
            
        except Exception as e:
            logger.warning(f"Frame encoding failed: {e}")
            return b''
    
    def get_next_frame(self, timeout: float = 0.1) -> Optional[VideoFrame]:
        """
        Get next video frame (for manual processing)
        
        Args:
            timeout: Timeout in seconds
        
        Returns:
            VideoFrame or None if timeout
        """
        # This would require a separate queue for manual access
        # For now, return None as frames are handled via callback
        return None
    
    def get_queue_size(self) -> int:
        """
        Get current frame queue size
        
        Returns:
            Number of frames in queue
        """
        return self.frame_queue.qsize()
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop_capture()


# Convenience functions

def create_video_stream(width: int = 640, height: int = 480, fps: int = 30) -> VideoStream:
    """
    Create and configure video stream
    
    Args:
        width: Frame width
        height: Frame height
        fps: Frames per second
    
    Returns:
        Configured VideoStream
    """
    config = VideoConfig(width=width, height=height, fps=fps)
    return VideoStream(config)


def list_video_devices() -> Dict[int, Dict[str, Any]]:
    """
    List available video devices
    
    Returns:
        Dictionary of device info
    """
    devices = {}
    for i in range(10):  # Check first 10 indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            devices[i] = {
                'name': f'Camera {i}',
                'width': width,
                'height': height,
                'fps': fps
            }
            cap.release()
    return devices