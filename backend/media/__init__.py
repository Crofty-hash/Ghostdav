"""Media package for real-time audio/video streaming"""

from .audio_stream import AudioStream, AudioConfig, AudioFrame, create_audio_stream, list_audio_devices
from .video_stream import VideoStream, VideoConfig, VideoFrame, create_video_stream, list_video_devices
from .media_utils import (
    calculate_audio_level, apply_audio_gain, detect_silence, normalize_audio_level,
    resize_video_frame, convert_color_space, calculate_frame_brightness,
    adjust_frame_brightness, detect_motion, add_timestamp_overlay,
    compress_frame_jpeg, calculate_stream_stats, create_test_audio_tone,
    create_test_video_pattern
)

__all__ = [
    'AudioStream',
    'AudioConfig',
    'AudioFrame',
    'create_audio_stream',
    'list_audio_devices',
    'VideoStream',
    'VideoConfig',
    'VideoFrame',
    'create_video_stream',
    'list_video_devices',
    'calculate_audio_level',
    'apply_audio_gain',
    'detect_silence',
    'normalize_audio_level',
    'resize_video_frame',
    'convert_color_space',
    'calculate_frame_brightness',
    'adjust_frame_brightness',
    'detect_motion',
    'add_timestamp_overlay',
    'compress_frame_jpeg',
    'calculate_stream_stats',
    'create_test_audio_tone',
    'create_test_video_pattern'
]
