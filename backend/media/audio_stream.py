"""
Audio Stream - Real-time microphone capture and streaming
WebRTC-compatible audio streaming for voice communication
"""

import pyaudio
import threading
import numpy as np
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
import logging
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio stream configuration"""
    sample_rate: int = 44100
    channels: int = 1
    chunk_size: int = 1024
    format: int = pyaudio.paInt16
    device_index: Optional[int] = None


@dataclass
class AudioFrame:
    """Audio frame data"""
    data: bytes
    timestamp: float
    sequence_number: int
    config: AudioConfig


class AudioStream:
    """Real-time audio capture and streaming"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """
        Initialize audio stream
        
        Args:
            config: Audio configuration
        """
        self.config = config or AudioConfig()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_streaming = False
        self.is_recording = False
        
        # Threading
        self.capture_thread = None
        self.process_thread = None
        
        # Queues
        self.audio_queue = queue.Queue(maxsize=100)
        self.frame_queue = queue.Queue(maxsize=50)
        
        # Callbacks
        self.frame_callback: Optional[Callable[[AudioFrame], None]] = None
        self.error_callback: Optional[Callable[[Exception], None]] = None
        
        # Sequence tracking
        self.frame_sequence = 0
        
        # Audio processing
        self.vad_enabled = False
        self.vad_threshold = 0.01  # Voice activity detection threshold
        
        logger.info(f"Audio stream initialized: {self.config.sample_rate}Hz, {self.config.channels}ch")
    
    def start_capture(self) -> bool:
        """
        Start audio capture from microphone
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.stream is not None:
                self.stop_capture()
            
            self.stream = self.audio.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.config.device_index,
                frames_per_buffer=self.config.chunk_size
            )
            
            self.is_streaming = True
            self.is_recording = True
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            # Start processing thread
            self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.process_thread.start()
            
            logger.info("Audio capture started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            if self.error_callback:
                self.error_callback(e)
            return False
    
    def stop_capture(self) -> None:
        """Stop audio capture"""
        self.is_recording = False
        self.is_streaming = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=1.0)
        
        logger.info("Audio capture stopped")
    
    def pause_stream(self) -> None:
        """Pause audio streaming (keep capture running)"""
        self.is_streaming = False
        logger.info("Audio streaming paused")
    
    def resume_stream(self) -> None:
        """Resume audio streaming"""
        self.is_streaming = True
        logger.info("Audio streaming resumed")
    
    def set_frame_callback(self, callback: Callable[[AudioFrame], None]) -> None:
        """
        Set callback for audio frames
        
        Args:
            callback: Function to call with each AudioFrame
        """
        self.frame_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """
        Set callback for errors
        
        Args:
            callback: Function to call on errors
        """
        self.error_callback = callback
    
    def enable_vad(self, threshold: float = 0.01) -> None:
        """
        Enable voice activity detection
        
        Args:
            threshold: VAD threshold (0.0-1.0)
        """
        self.vad_enabled = True
        self.vad_threshold = threshold
        logger.info(f"VAD enabled with threshold {threshold}")
    
    def disable_vad(self) -> None:
        """Disable voice activity detection"""
        self.vad_enabled = False
        logger.info("VAD disabled")
    
    def get_audio_devices(self) -> Dict[int, Dict[str, Any]]:
        """
        Get list of available audio input devices
        
        Returns:
            Dictionary of device index -> device info
        """
        devices = {}
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:
                devices[i] = {
                    'name': info.get('name', 'Unknown'),
                    'channels': info.get('maxInputChannels', 0),
                    'sample_rate': int(info.get('defaultSampleRate', 44100))
                }
        return devices
    
    def _capture_loop(self) -> None:
        """Main audio capture loop"""
        try:
            while self.is_recording:
                if self.stream and not self.stream.is_stopped():
                    # Read audio data
                    data = self.stream.read(self.config.chunk_size, exception_on_overflow=False)
                    
                    # Put in queue (non-blocking)
                    try:
                        self.audio_queue.put(data, timeout=0.1)
                    except queue.Full:
                        # Drop oldest frame if queue is full
                        try:
                            self.audio_queue.get_nowait()
                            self.audio_queue.put(data, timeout=0.1)
                        except queue.Empty:
                            pass
                else:
                    time.sleep(0.01)
                    
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            if self.error_callback:
                self.error_callback(e)
    
    def _process_loop(self) -> None:
        """Audio processing and frame generation loop"""
        try:
            while self.is_recording:
                try:
                    # Get audio data from queue
                    data = self.audio_queue.get(timeout=0.1)
                    
                    # Process audio data
                    if self._should_process_frame(data):
                        frame = self._create_frame(data)
                        
                        # Put in frame queue
                        try:
                            self.frame_queue.put(frame, timeout=0.1)
                            
                            # Call callback if streaming
                            if self.is_streaming and self.frame_callback:
                                self.frame_callback(frame)
                                
                        except queue.Full:
                            # Drop frame if queue is full
                            pass
                    
                except queue.Empty:
                    continue
                    
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            if self.error_callback:
                self.error_callback(e)
    
    def _should_process_frame(self, data: bytes) -> bool:
        """
        Determine if frame should be processed (VAD check)
        
        Args:
            data: Audio data
        
        Returns:
            True if should process, False otherwise
        """
        if not self.vad_enabled:
            return True
        
        # Convert to numpy array for analysis
        audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_array ** 2))
        
        return rms > self.vad_threshold
    
    def _create_frame(self, data: bytes) -> AudioFrame:
        """
        Create AudioFrame from raw data
        
        Args:
            data: Raw audio data
        
        Returns:
            AudioFrame object
        """
        self.frame_sequence += 1
        
        return AudioFrame(
            data=data,
            timestamp=time.time(),
            sequence_number=self.frame_sequence,
            config=self.config
        )
    
    def get_next_frame(self, timeout: float = 0.1) -> Optional[AudioFrame]:
        """
        Get next audio frame from queue
        
        Args:
            timeout: Timeout in seconds
        
        Returns:
            AudioFrame or None if timeout
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
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
        if self.audio:
            self.audio.terminate()


# Convenience functions

def create_audio_stream(sample_rate: int = 44100, channels: int = 1) -> AudioStream:
    """
    Create and configure audio stream
    
    Args:
        sample_rate: Audio sample rate
        channels: Number of channels
    
    Returns:
        Configured AudioStream
    """
    config = AudioConfig(sample_rate=sample_rate, channels=channels)
    return AudioStream(config)


def list_audio_devices() -> Dict[int, Dict[str, Any]]:
    """
    List available audio input devices
    
    Returns:
        Dictionary of device info
    """
    temp_audio = pyaudio.PyAudio()
    devices = {}
    
    for i in range(temp_audio.get_device_count()):
        info = temp_audio.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            devices[i] = {
                'name': info.get('name', 'Unknown'),
                'channels': info.get('maxInputChannels', 0),
                'sample_rate': int(info.get('defaultSampleRate', 44100))
            }
    
    temp_audio.terminate()
    return devices