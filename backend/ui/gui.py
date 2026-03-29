"""
GUI - Cross-platform desktop client for GhostDav
Main GUI application with chat, file sharing, and media streaming
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import os
from typing import Optional, Callable, Dict, Any
from PIL import Image
import base64
import logging

from .main_window import MainWindow
from .widgets import MediaControlPanel, FileTransferWidget, SteganographyWidget, ConnectionStatusWidget, SettingsDialog, configure_styles
from ..networking import SocketClient
from ..media import AudioStream, VideoStream, list_audio_devices, list_video_devices
from ..core import Steganographer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GhostDavGUI:
    """Main GUI application for GhostDav desktop client"""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 8888):
        """
        Initialize GUI application
        
        Args:
            server_host: GhostDav server hostname
            server_port: GhostDav server port
        """
        self.server_host = server_host
        self.server_port = server_port
        
        # Core components
        self.client: Optional[SocketClient] = None
        self.audio_stream: Optional[AudioStream] = None
        self.video_stream: Optional[VideoStream] = None
        self.steganographer = Steganographer()
        
        # UI state
        self.is_connected = False
        self.current_chat_peer = None
        self.media_streams_active = False
        
        # Settings
        self.settings = {
            "username": "Anonymous",
            "theme": "System",
            "auto_connect": False,
            "port": server_port,
            "max_peers": 10,
            "timeout": 30,
            "encryption": "ChaCha20",
            "key_rotation": True,
            "stego_padding": 1024
        }
        
        # Configure styles
        configure_styles()
        
        # Create main window
        self.root = tk.Tk()
        self.main_window = MainWindow(self.root, self)
        
        # Create custom widgets
        self._create_custom_widgets()
        
        # Setup callbacks
        self._setup_callbacks()
        
        logger.info("GhostDav GUI initialized")
    
    def _create_custom_widgets(self) -> None:
        """Create and integrate custom widgets"""
        # Connection status widget in toolbar
        self.connection_status = ConnectionStatusWidget(self.main_window.root)
        # Note: This would need to be integrated into the toolbar layout
        
        # Media control panel (could be added to a separate tab or window)
        self.media_panel = MediaControlPanel(self.main_window.root, "Media Controls")
        self.media_panel.set_audio_callback(self._toggle_audio_stream)
        self.media_panel.set_video_callback(self._toggle_video_stream)
        
        # File transfer widget (could be added to chat panel)
        self.file_widget = FileTransferWidget(self.main_window.root, "File Transfers")
        
        # Steganography widget (could be added to a tools window)
        self.stego_widget = SteganographyWidget(self.main_window.root, "Steganography")
        self.stego_widget.set_hide_callback(self._handle_stego_hide)
        self.stego_widget.set_reveal_callback(self._handle_stego_reveal)
    
    def run(self) -> None:
        """Start the GUI application"""
        self.root.mainloop()
    
    def connect_to_server(self) -> bool:
        """
        Connect to GhostDav server
        
        Returns:
            True if connected successfully
        """
        try:
            client_id = f"desktop_{int(time.time())}"
            self.client = SocketClient(client_id, self.server_host, self.server_port)
            
            # Set message handlers
            self.client.message_handlers = {
                'peer_message': self._handle_peer_message,
                'connect': self._handle_connect,
                'disconnect': self._handle_disconnect,
                'heartbeat': self._handle_heartbeat
            }
            
            if self.client.connect():
                self.is_connected = True
                self.main_window.update_connection_status(True)
                logger.info(f"Connected to server as {client_id}")
                return True
            else:
                self.main_window.show_error("Connection Failed", "Could not connect to server")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.main_window.show_error("Connection Error", str(e))
            return False
    
    def disconnect_from_server(self) -> None:
        """Disconnect from server"""
        if self.client:
            self.client.disconnect()
            self.client = None
        
        self.is_connected = False
        self.main_window.update_connection_status(False)
        logger.info("Disconnected from server")
    
    def send_chat_message(self, message: str, recipient: Optional[str] = None) -> None:
        """
        Send chat message
        
        Args:
            message: Message text
            recipient: Recipient peer ID (None for broadcast)
        """
        if not self.is_connected or not self.client:
            self.main_window.show_error("Not Connected", "Please connect to server first")
            return
        
        try:
            # For now, simulate sending message
            # In real implementation, this would use the network client
            self.main_window.add_chat_message("You", message, is_own=True)
            logger.info(f"Sent message: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.main_window.show_error("Send Error", str(e))
    
    def start_audio_stream(self) -> bool:
        """
        Start audio streaming
        
        Returns:
            True if started successfully
        """
        try:
            if self.audio_stream is None:
                self.audio_stream = AudioStream()
                self.audio_stream.set_frame_callback(self._handle_audio_frame)
                self.audio_stream.set_error_callback(self._handle_audio_error)
            
            if self.audio_stream.start_capture():
                self.media_streams_active = True
                self.main_window.update_media_status(audio=True)
                logger.info("Audio streaming started")
                return True
            else:
                self.main_window.show_error("Audio Error", "Failed to start audio capture")
                return False
                
        except Exception as e:
            logger.error(f"Audio stream error: {e}")
            self.main_window.show_error("Audio Error", str(e))
            return False
    
    def stop_audio_stream(self) -> None:
        """Stop audio streaming"""
        if self.audio_stream:
            self.audio_stream.stop_capture()
            self.audio_stream = None
        
        self.media_streams_active = False
        self.main_window.update_media_status(audio=False)
        logger.info("Audio streaming stopped")
    
    def start_video_stream(self) -> bool:
        """
        Start video streaming
        
        Returns:
            True if started successfully
        """
        try:
            if self.video_stream is None:
                self.video_stream = VideoStream()
                self.video_stream.set_frame_callback(self._handle_video_frame)
                self.video_stream.set_error_callback(self._handle_video_error)
            
            if self.video_stream.start_capture():
                self.media_streams_active = True
                self.main_window.update_media_status(video=True)
                logger.info("Video streaming started")
                return True
            else:
                self.main_window.show_error("Video Error", "Failed to start video capture")
                return False
                
        except Exception as e:
            logger.error(f"Video stream error: {e}")
            self.main_window.show_error("Video Error", str(e))
            return False
    
    def stop_video_stream(self) -> None:
        """Stop video streaming"""
        if self.video_stream:
            self.video_stream.stop_capture()
            self.video_stream = None
        
        self.media_streams_active = False
        self.main_window.update_media_status(video=False)
        logger.info("Video streaming stopped")
    
    def send_file(self, file_path: str) -> None:
        """
        Send file with optional steganography
        
        Args:
            file_path: Path to file to send
        """
        if not os.path.exists(file_path):
            self.main_window.show_error("File Error", "File not found")
            return
        
        filename = os.path.basename(file_path)
        transfer_id = f"send_{int(time.time())}"
        
        # Add to file transfer widget
        self.file_widget.add_transfer(transfer_id, filename, "preparing")
        
        # Show steganography option
        use_stego = messagebox.askyesno(
            "Steganography",
            "Hide file in an image? (Select carrier image next)"
        )
        
        carrier_image = None
        if use_stego:
            carrier_image = filedialog.askopenfilename(
                title="Select Carrier Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
            )
            if not carrier_image:
                self.file_widget.update_status(transfer_id, "cancelled")
                return
        
        # Update status
        self.file_widget.update_status(transfer_id, "sending")
        
        # For now, simulate file sending
        # In real implementation, this would use file_sender
        def simulate_send():
            for progress in range(0, 101, 10):
                time.sleep(0.1)
                self.file_widget.update_progress(transfer_id, progress)
            
            self.file_widget.update_status(transfer_id, "completed")
            self.main_window.add_system_message(f"File sent: {filename}")
            logger.info(f"File send completed: {filename}")
        
        # Run in background thread
        threading.Thread(target=simulate_send, daemon=True).start()
    
    def receive_file(self) -> None:
        """Receive incoming file"""
        # For now, simulate file reception
        # In real implementation, this would use file_receiver
        
        filename = "received_example.txt"
        transfer_id = f"recv_{int(time.time())}"
        
        # Add to file transfer widget
        self.file_widget.add_transfer(transfer_id, filename, "receiving")
        
        def simulate_receive():
            for progress in range(0, 101, 15):
                time.sleep(0.2)
                self.file_widget.update_progress(transfer_id, progress)
            
            self.file_widget.update_status(transfer_id, "completed")
            self.main_window.add_system_message(f"File received: {filename}")
            logger.info(f"File reception completed: {filename}")
        
        # Run in background thread
        threading.Thread(target=simulate_receive, daemon=True).start()
    
    def hide_message_in_image(self) -> None:
        """Hide text message in image using steganography"""
        # Use the steganography widget
        # This method is now called from main window, but delegates to widget
        self.stego_widget._hide_message()
    
    def reveal_message_from_image(self) -> None:
        """Extract hidden message from image"""
        # Use the steganography widget
        # This method is now called from main window, but delegates to widget
        self.stego_widget._reveal_message()
    
    def show_device_settings(self) -> None:
        """Show audio/video device settings"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Device Settings")
        settings_window.geometry("400x300")
        
        # Audio devices
        ttk.Label(settings_window, text="Audio Devices:").pack(pady=5)
        audio_devices = list_audio_devices()
        audio_var = tk.StringVar()
        
        if audio_devices:
            for idx, info in audio_devices.items():
                ttk.Radiobutton(
                    settings_window, 
                    text=f"{idx}: {info['name']}",
                    variable=audio_var,
                    value=str(idx)
                ).pack(anchor=tk.W, padx=20)
        else:
            ttk.Label(settings_window, text="No audio devices found").pack()
        
        # Video devices
        ttk.Label(settings_window, text="Video Devices:").pack(pady=5)
        video_devices = list_video_devices()
        video_var = tk.StringVar()
        
        if video_devices:
            for idx, info in video_devices.items():
                ttk.Radiobutton(
                    settings_window, 
                    text=f"{idx}: {info['name']} ({info['width']}x{info['height']})",
                    variable=video_var,
                    value=str(idx)
                ).pack(anchor=tk.W, padx=20)
        else:
            ttk.Label(settings_window, text="No video devices found").pack()
        
        # Close button
        ttk.Button(settings_window, text="Close", 
                  command=settings_window.destroy).pack(pady=10)
    
    def _save_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        Save updated settings
        
        Args:
            new_settings: New settings dictionary
        """
        self.settings.update(new_settings)
        logger.info(f"Settings updated: {new_settings}")
        # In real implementation, save to file or database
    
    def _handle_stego_hide(self, image_path: str, message: str) -> None:
        """
        Handle steganography hide operation from widget
        
        Args:
            image_path: Path to carrier image
            message: Message to hide
        """
        try:
            # Get output path
            output_path = filedialog.asksaveasfilename(
                title="Save Stego Image",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )
            if not output_path:
                return
            
            # Hide message
            result = self.steganographer.embed_message(image_path, message, output_path)
            
            if result.success:
                result_text = f"Message hidden successfully in {os.path.basename(result.image_path)}"
                self.stego_widget.show_result(result_text)
                self.main_window.show_info("Success", result_text)
                logger.info(f"Message hidden in image: {result.image_path}")
            else:
                self.stego_widget.show_result(f"Error: {result.error}")
                self.main_window.show_error("Stego Error", result.error)
                
        except Exception as e:
            error_msg = f"Steganography error: {e}"
            self.stego_widget.show_result(error_msg)
            logger.error(error_msg)
            self.main_window.show_error("Stego Error", str(e))
    
    def _handle_stego_reveal(self, image_path: str) -> None:
        """
        Handle steganography reveal operation from widget
        
        Args:
            image_path: Path to stego image
        """
        try:
            # Extract message
            message = self.steganographer.extract_message(image_path)
            
            if message:
                result_text = f"Hidden message found: {message}"
                self.stego_widget.show_result(result_text)
                self.main_window.show_info("Hidden Message", f"Found: {message}")
                logger.info(f"Message extracted from image: {message[:50]}...")
            else:
                result_text = "No hidden message found in image"
                self.stego_widget.show_result(result_text)
                self.main_window.show_info("No Message", result_text)
                
        except Exception as e:
            error_msg = f"Message extraction error: {e}"
            self.stego_widget.show_result(error_msg)
            logger.error(error_msg)
            self.main_window.show_error("Extract Error", str(e))
    
    def show_settings_dialog(self) -> None:
        """Show main settings dialog"""
        SettingsDialog(self.root, self.settings, self._save_settings)
    
    def show_settings_dialog(self) -> None:
        """Show main settings dialog"""
        SettingsDialog(self.root, self.settings, self._save_settings)
    
    def _setup_callbacks(self) -> None:
        """Setup UI callbacks"""
        # Connect main window actions to GUI methods
        self.main_window.set_connect_callback(self.connect_to_server)
        self.main_window.set_disconnect_callback(self.disconnect_from_server)
        self.main_window.set_send_callback(self.send_chat_message)
        self.main_window.set_audio_callback(self._toggle_audio_stream)
        self.main_window.set_video_callback(self._toggle_video_stream)
        self.main_window.set_file_send_callback(self.send_file)
        self.main_window.set_file_receive_callback(self.receive_file)
        self.main_window.set_stego_hide_callback(self.hide_message_in_image)
        self.main_window.set_stego_reveal_callback(self.reveal_message_from_image)
        self.main_window.set_settings_callback(self.show_settings_dialog)
    
    def _toggle_audio_stream(self) -> None:
        """Toggle audio streaming"""
        if self.audio_stream and self.audio_stream.is_streaming:
            self.stop_audio_stream()
        else:
            self.start_audio_stream()
    
    def _toggle_video_stream(self) -> None:
        """Toggle video streaming"""
        if self.video_stream and self.video_stream.is_streaming:
            self.stop_video_stream()
        else:
            self.start_video_stream()
    
    def _handle_peer_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming peer message"""
        # Process incoming message and display in UI
        sender = message.get('sender', 'Unknown')
        content = message.get('content', '')
        self.main_window.add_chat_message(sender, content)
    
    def _handle_connect(self, data: Dict[str, Any]) -> None:
        """Handle connection event"""
        peer_id = data.get('peer_id', 'Unknown')
        self.main_window.add_system_message(f"Peer connected: {peer_id}")
    
    def _handle_disconnect(self, data: Dict[str, Any]) -> None:
        """Handle disconnection event"""
        peer_id = data.get('peer_id', 'Unknown')
        self.main_window.add_system_message(f"Peer disconnected: {peer_id}")
    
    def _handle_heartbeat(self, data: Dict[str, Any]) -> None:
        """Handle heartbeat (keep connection alive)"""
        # Update connection status
        pass
    
    def _handle_audio_frame(self, frame) -> None:
        """Handle incoming audio frame"""
        # Process audio frame (e.g., send over network, play locally)
        # For now, just log
        logger.debug(f"Audio frame received: {len(frame.data)} bytes")
    
    def _handle_video_frame(self, frame) -> None:
        """Handle incoming video frame"""
        # Process video frame (e.g., display, send over network)
        # For now, just log
        logger.debug(f"Video frame received: {frame.data.shape}")
    
    def _handle_audio_error(self, error: Exception) -> None:
        """Handle audio streaming error"""
        logger.error(f"Audio error: {error}")
        self.main_window.show_error("Audio Error", str(error))
        self.stop_audio_stream()
    
    def _handle_video_error(self, error: Exception) -> None:
        """Handle video streaming error"""
        logger.error(f"Video error: {error}")
        self.main_window.show_error("Video Error", str(error))
        self.stop_video_stream()


# Convenience function to run the GUI
def run_gui(server_host: str = 'localhost', server_port: int = 8888) -> None:
    """
    Run the GhostDav GUI application
    
    Args:
        server_host: Server hostname
        server_port: Server port
    """
    app = GhostDavGUI(server_host, server_port)
    app.run()