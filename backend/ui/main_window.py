"""
Main Window - Primary GUI window for GhostDav desktop client
Contains chat interface, media controls, and file sharing
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
from typing import Optional, Callable, Dict, Any
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window with chat and media controls"""
    
    def __init__(self, root: tk.Tk, gui_app):
        """
        Initialize main window
        
        Args:
            root: Tkinter root window
            gui_app: Parent GUI application
        """
        self.root = root
        self.gui_app = gui_app
        
        # Window setup
        self.root.title("GhostDav - Secure P2P Communication")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Callbacks
        self.connect_callback: Optional[Callable] = None
        self.disconnect_callback: Optional[Callable] = None
        self.send_callback: Optional[Callable] = None
        self.audio_callback: Optional[Callable] = None
        self.video_callback: Optional[Callable] = None
        self.file_send_callback: Optional[Callable] = None
        self.file_receive_callback: Optional[Callable] = None
        self.stego_hide_callback: Optional[Callable] = None
        self.stego_reveal_callback: Optional[Callable] = None
        self.settings_callback: Optional[Callable] = None
        
        # UI state
        self.audio_active = False
        self.video_active = False
        
        self._setup_ui()
        self._setup_menu()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self) -> None:
        """Setup the main UI components"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create toolbar
        self._create_toolbar(main_frame)
        
        # Create main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Split into left (chat) and right (media) panels
        self._create_chat_panel(content_frame)
        self._create_media_panel(content_frame)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Disconnected")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def _create_toolbar(self, parent) -> None:
        """Create toolbar with connection and media controls"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Connection buttons
        self.connect_btn = ttk.Button(toolbar, text="Connect", command=self._on_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(toolbar, text="Disconnect", command=self._on_disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Media controls
        self.audio_btn = ttk.Button(toolbar, text="🎤 Audio", command=self._on_toggle_audio)
        self.audio_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.video_btn = ttk.Button(toolbar, text="📹 Video", command=self._on_toggle_video)
        self.video_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # File operations
        ttk.Button(toolbar, text="📁 Send File", command=self._on_send_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="📥 Receive File", command=self._on_receive_file).pack(side=tk.LEFT, padx=(0, 5))
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Steganography
        ttk.Button(toolbar, text="🖼️ Hide Message", command=self._on_stego_hide).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="🔍 Reveal Message", command=self._on_stego_reveal).pack(side=tk.LEFT)
    
    def _create_chat_panel(self, parent) -> None:
        """Create chat interface panel"""
        # Chat frame (left side)
        chat_frame = ttk.LabelFrame(parent, text="Chat", padding=5)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Chat display
        self.chat_text = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=20)
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        self.chat_text.config(state=tk.DISABLED)
        
        # Message input frame
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Message entry
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", lambda e: self._on_send_message())
        
        # Send button
        ttk.Button(input_frame, text="Send", command=self._on_send_message).pack(side=tk.RIGHT, padx=(5, 0))
    
    def _create_media_panel(self, parent) -> None:
        """Create media display panel"""
        # Media frame (right side)
        media_frame = ttk.LabelFrame(parent, text="Media", padding=5)
        media_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Media display area (placeholder for video)
        self.media_canvas = tk.Canvas(media_frame, bg='black', width=320, height=240)
        self.media_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Media status
        status_frame = ttk.Frame(media_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.audio_status = ttk.Label(status_frame, text="🎤 Audio: Off")
        self.audio_status.pack(side=tk.LEFT, padx=(0, 10))
        
        self.video_status = ttk.Label(status_frame, text="📹 Video: Off")
        self.video_status.pack(side=tk.LEFT)
    
    def _setup_menu(self) -> None:
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self._on_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Device Settings", command=self._on_device_settings)
        tools_menu.add_command(label="Clear Chat", command=self._on_clear_chat)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._on_about)
    
    def update_connection_status(self, connected: bool) -> None:
        """
        Update connection status display
        
        Args:
            connected: True if connected, False otherwise
        """
        if connected:
            self.status_var.set("Connected")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
        else:
            self.status_var.set("Disconnected")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
    
    def update_media_status(self, audio: Optional[bool] = None, video: Optional[bool] = None) -> None:
        """
        Update media status display
        
        Args:
            audio: Audio streaming status
            video: Video streaming status
        """
        if audio is not None:
            self.audio_active = audio
            status = "On" if audio else "Off"
            self.audio_status.config(text=f"🎤 Audio: {status}")
            self.audio_btn.config(text="🎤 Stop Audio" if audio else "🎤 Start Audio")
        
        if video is not None:
            self.video_active = video
            status = "On" if video else "Off"
            self.video_status.config(text=f"📹 Video: {status}")
            self.video_btn.config(text="📹 Stop Video" if video else "📹 Start Video")
    
    def add_chat_message(self, sender: str, message: str, is_own: bool = False) -> None:
        """
        Add message to chat display
        
        Args:
            sender: Message sender
            message: Message content
            is_own: True if message is from current user
        """
        self.chat_text.config(state=tk.NORMAL)
        
        timestamp = time.strftime("%H:%M:%S")
        prefix = "You" if is_own else sender
        
        self.chat_text.insert(tk.END, f"[{timestamp}] {prefix}: {message}\n")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def add_system_message(self, message: str) -> None:
        """
        Add system message to chat
        
        Args:
            message: System message
        """
        self.chat_text.config(state=tk.NORMAL)
        
        timestamp = time.strftime("%H:%M:%S")
        self.chat_text.insert(tk.END, f"[{timestamp}] *** {message} ***\n")
        self.chat_text.tag_add("system", "end-2l", "end-1c")
        self.chat_text.tag_config("system", foreground="blue", font=("TkDefaultFont", 9, "italic"))
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def show_error(self, title: str, message: str) -> None:
        """
        Show error dialog
        
        Args:
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str) -> None:
        """
        Show info dialog
        
        Args:
            title: Dialog title
            message: Info message
        """
        messagebox.showinfo(title, message)
    
    def get_text_input(self, prompt: str) -> Optional[str]:
        """
        Get text input from user
        
        Args:
            prompt: Input prompt
        
        Returns:
            User input or None if cancelled
        """
        return simpledialog.askstring("Input", prompt)
    
    def set_connect_callback(self, callback: Callable) -> None:
        """Set connect button callback"""
        self.connect_callback = callback
    
    def set_disconnect_callback(self, callback: Callable) -> None:
        """Set disconnect button callback"""
        self.disconnect_callback = callback
    
    def set_send_callback(self, callback: Callable) -> None:
        """Set send message callback"""
        self.send_callback = callback
    
    def set_audio_callback(self, callback: Callable) -> None:
        """Set audio toggle callback"""
        self.audio_callback = callback
    
    def set_video_callback(self, callback: Callable) -> None:
        """Set video toggle callback"""
        self.video_callback = callback
    
    def set_file_send_callback(self, callback: Callable) -> None:
        """Set file send callback"""
        self.file_send_callback = callback
    
    def set_file_receive_callback(self, callback: Callable) -> None:
        """Set file receive callback"""
        self.file_receive_callback = callback
    
    def set_stego_hide_callback(self, callback: Callable) -> None:
        """Set stego hide callback"""
        self.stego_hide_callback = callback
    
    def set_stego_reveal_callback(self, callback: Callable) -> None:
        """Set stego reveal callback"""
        self.stego_reveal_callback = callback
    
    def set_settings_callback(self, callback: Callable) -> None:
        """Set settings callback"""
        self.settings_callback = callback
    
    def _on_connect(self) -> None:
        """Handle connect button"""
        if self.connect_callback:
            self.connect_callback()
    
    def _on_disconnect(self) -> None:
        """Handle disconnect button"""
        if self.disconnect_callback:
            self.disconnect_callback()
    
    def _on_send_message(self) -> None:
        """Handle send message"""
        message = self.message_entry.get().strip()
        if message and self.send_callback:
            self.send_callback(message)
            self.message_entry.delete(0, tk.END)
    
    def _on_toggle_audio(self) -> None:
        """Handle audio toggle"""
        if self.audio_callback:
            self.audio_callback()
    
    def _on_toggle_video(self) -> None:
        """Handle video toggle"""
        if self.video_callback:
            self.video_callback()
    
    def _on_send_file(self) -> None:
        """Handle file send"""
        if self.file_send_callback:
            # In real implementation, show file dialog
            # For now, just call callback with dummy path
            self.file_send_callback("dummy_file.txt")
    
    def _on_receive_file(self) -> None:
        """Handle file receive"""
        if self.file_receive_callback:
            self.file_receive_callback()
    
    def _on_stego_hide(self) -> None:
        """Handle stego hide"""
        if self.stego_hide_callback:
            self.stego_hide_callback()
    
    def _on_stego_reveal(self) -> None:
        """Handle stego reveal"""
        if self.stego_reveal_callback:
            self.stego_reveal_callback()
    
    def _on_settings(self) -> None:
        """Handle settings menu"""
        if self.settings_callback:
            self.settings_callback()
    
    def _on_device_settings(self) -> None:
        """Handle device settings menu"""
        # Show device settings dialog
        self.gui_app.show_device_settings()
    
    def _on_clear_chat(self) -> None:
        """Handle clear chat"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _on_about(self) -> None:
        """Handle about dialog"""
        about_text = """GhostDav - Secure P2P Communication

A privacy-focused peer-to-peer communication platform
with end-to-end encryption and steganography.

Version: 1.0 (Beta)
Features:
• Encrypted messaging
• File sharing with steganography
• Real-time audio/video streaming
• Anonymous routing
"""
        messagebox.showinfo("About GhostDav", about_text)
    
    def _on_exit(self) -> None:
        """Handle application exit"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.quit()