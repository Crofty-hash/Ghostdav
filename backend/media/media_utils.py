"""
Media Utils - Helper functions for audio/video processing
Optional utilities for media stream enhancement and analysis
"""

import numpy as np
import cv2
from typing import Optional, Tuple, List
import math
import time


def calculate_audio_level(audio_data: bytes, sample_width: int = 2) -> float:
    """
    Calculate audio level (RMS) from raw audio data
    
    Args:
        audio_data: Raw audio bytes
        sample_width: Bytes per sample (1, 2, or 4)
    
    Returns:
        RMS audio level (0.0 to 1.0)
    """
    if sample_width == 1:
        # 8-bit unsigned
        samples = np.frombuffer(audio_data, dtype=np.uint8)
        samples = (samples - 128) / 128.0  # Convert to -1.0 to 1.0
    elif sample_width == 2:
        # 16-bit signed
        samples = np.frombuffer(audio_data, dtype=np.int16)
        samples = samples / 32768.0
    elif sample_width == 4:
        # 32-bit float
        samples = np.frombuffer(audio_data, dtype=np.float32)
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")
    
    # Calculate RMS
    rms = np.sqrt(np.mean(samples ** 2))
    return min(rms, 1.0)  # Clamp to 1.0


def apply_audio_gain(audio_data: bytes, gain_db: float, sample_width: int = 2) -> bytes:
    """
    Apply gain to audio data
    
    Args:
        audio_data: Raw audio bytes
        gain_db: Gain in decibels
        sample_width: Bytes per sample
    
    Returns:
        Processed audio bytes
    """
    gain_linear = 10 ** (gain_db / 20.0)
    
    if sample_width == 2:
        samples = np.frombuffer(audio_data, dtype=np.int16)
        samples = np.clip(samples * gain_linear, -32768, 32767).astype(np.int16)
    elif sample_width == 4:
        samples = np.frombuffer(audio_data, dtype=np.float32)
        samples = np.clip(samples * gain_linear, -1.0, 1.0).astype(np.float32)
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")
    
    return samples.tobytes()


def detect_silence(audio_data: bytes, threshold: float = 0.01, sample_width: int = 2) -> bool:
    """
    Detect if audio data contains silence
    
    Args:
        audio_data: Raw audio bytes
        threshold: Silence threshold (0.0 to 1.0)
        sample_width: Bytes per sample
    
    Returns:
        True if silence detected
    """
    level = calculate_audio_level(audio_data, sample_width)
    return level < threshold


def normalize_audio_level(audio_data: bytes, target_level: float = 0.7,
                         sample_width: int = 2) -> bytes:
    """
    Normalize audio to target level
    
    Args:
        audio_data: Raw audio bytes
        target_level: Target RMS level
        sample_width: Bytes per sample
    
    Returns:
        Normalized audio bytes
    """
    current_level = calculate_audio_level(audio_data, sample_width)
    
    if current_level == 0:
        return audio_data
    
    gain_db = 20 * math.log10(target_level / current_level)
    return apply_audio_gain(audio_data, gain_db, sample_width)


def resize_video_frame(frame: np.ndarray, target_width: int, target_height: int,
                      interpolation: int = cv2.INTER_LINEAR) -> np.ndarray:
    """
    Resize video frame
    
    Args:
        frame: Input video frame
        target_width: Target width
        target_height: Target height
        interpolation: OpenCV interpolation method
    
    Returns:
        Resized frame
    """
    return cv2.resize(frame, (target_width, target_height), interpolation=interpolation)


def convert_color_space(frame: np.ndarray, from_space: str = 'BGR',
                       to_space: str = 'RGB') -> np.ndarray:
    """
    Convert video frame color space
    
    Args:
        frame: Input video frame
        from_space: Source color space
        to_space: Target color space
    
    Returns:
        Converted frame
    """
    conversion_map = {
        ('BGR', 'RGB'): cv2.COLOR_BGR2RGB,
        ('BGR', 'GRAY'): cv2.COLOR_BGR2GRAY,
        ('RGB', 'BGR'): cv2.COLOR_RGB2BGR,
        ('RGB', 'GRAY'): cv2.COLOR_RGB2GRAY,
        ('GRAY', 'RGB'): cv2.COLOR_GRAY2RGB,
        ('GRAY', 'BGR'): cv2.COLOR_GRAY2BGR,
    }
    
    key = (from_space, to_space)
    if key not in conversion_map:
        raise ValueError(f"Unsupported color space conversion: {from_space} -> {to_space}")
    
    return cv2.cvtColor(frame, conversion_map[key])


def calculate_frame_brightness(frame: np.ndarray) -> float:
    """
    Calculate average brightness of video frame
    
    Args:
        frame: Video frame
    
    Returns:
        Average brightness (0.0 to 1.0)
    """
    if len(frame.shape) == 3:
        # Color image - convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    
    return np.mean(gray) / 255.0


def adjust_frame_brightness(frame: np.ndarray, brightness_factor: float) -> np.ndarray:
    """
    Adjust frame brightness
    
    Args:
        frame: Video frame
        brightness_factor: Brightness adjustment factor (>1 brighter, <1 darker)
    
    Returns:
        Adjusted frame
    """
    return cv2.convertScaleAbs(frame, alpha=brightness_factor, beta=0)


def detect_motion(frame1: np.ndarray, frame2: np.ndarray, threshold: int = 25,
                 min_area: int = 500) -> Tuple[bool, List]:
    """
    Detect motion between two frames
    
    Args:
        frame1: First frame
        frame2: Second frame
        threshold: Motion detection threshold
        min_area: Minimum contour area to consider
    
    Returns:
        Tuple of (motion_detected, motion_contours)
    """
    # Convert to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Blur for noise reduction
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
    gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
    
    # Calculate difference
    frame_delta = cv2.absdiff(gray1, gray2)
    thresh = cv2.threshold(frame_delta, threshold, 255, cv2.THRESH_BINARY)[1]
    
    # Dilate threshold
    thresh = cv2.dilate(thresh, None, iterations=2)
    
    # Find contours
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by area
    motion_contours = [c for c in contours if cv2.contourArea(c) > min_area]
    
    return len(motion_contours) > 0, motion_contours


def add_timestamp_overlay(frame: np.ndarray, timestamp: Optional[float] = None,
                         position: Tuple[int, int] = (10, 30)) -> np.ndarray:
    """
    Add timestamp overlay to video frame
    
    Args:
        frame: Video frame
        timestamp: Timestamp (uses current time if None)
        position: Text position (x, y)
    
    Returns:
        Frame with timestamp overlay
    """
    if timestamp is None:
        timestamp = time.time()
    
    time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
    
    # Add text overlay
    cv2.putText(frame, time_str, position, cv2.FONT_HERSHEY_SIMPLEX,
               1, (255, 255, 255), 2, cv2.LINE_AA)
    
    return frame


def compress_frame_jpeg(frame: np.ndarray, quality: int = 80) -> bytes:
    """
    Compress video frame as JPEG
    
    Args:
        frame: Video frame
        quality: JPEG quality (0-100)
    
    Returns:
        JPEG compressed data
    """
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, encoded_img = cv2.imencode('.jpg', frame, encode_param)
    return encoded_img.tobytes()


def calculate_stream_stats(frames_processed: int, start_time: float,
                          current_time: Optional[float] = None) -> Dict:
    """
    Calculate streaming statistics
    
    Args:
        frames_processed: Number of frames processed
        start_time: Stream start time
        current_time: Current time (uses time.time() if None)
    
    Returns:
        Statistics dictionary
    """
    if current_time is None:
        current_time = time.time()
    
    duration = current_time - start_time
    
    return {
        'frames_processed': frames_processed,
        'duration_seconds': duration,
        'fps': frames_processed / duration if duration > 0 else 0,
        'total_time': duration
    }


def create_test_audio_tone(frequency: float = 440.0, duration: float = 1.0,
                          sample_rate: int = 44100, amplitude: float = 0.5) -> bytes:
    """
    Create test audio tone (sine wave)
    
    Args:
        frequency: Tone frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate
        amplitude: Amplitude (0.0 to 1.0)
    
    Returns:
        Raw audio bytes (16-bit signed)
    """
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, False)
    
    # Generate sine wave
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit signed integers
    tone_int16 = (tone * 32767).astype(np.int16)
    
    return tone_int16.tobytes()


def create_test_video_pattern(width: int = 640, height: int = 480,
                            pattern: str = 'checkerboard') -> np.ndarray:
    """
    Create test video pattern
    
    Args:
        width: Frame width
        height: Frame height
        pattern: Pattern type ('checkerboard', 'gradient', 'noise')
    
    Returns:
        Test video frame
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    if pattern == 'checkerboard':
        # Create checkerboard pattern
        square_size = 50
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                color = 255 if ((x // square_size) + (y // square_size)) % 2 == 0 else 0
                frame[y:y+square_size, x:x+square_size] = color
    
    elif pattern == 'gradient':
        # Create color gradient
        for y in range(height):
            for x in range(width):
                frame[y, x] = [x * 255 // width, y * 255 // height, 128]
    
    elif pattern == 'noise':
        # Create random noise
        frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    
    return frame