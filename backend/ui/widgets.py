"""
Custom UI Widgets - Specialized components for GhostDav GUI
Includes chat bubbles, media controls, and settings panels
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Optional, Callable, Dict, Any, List
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatBubble(ttk.Frame):
    """Custom chat message bubble widget"""
    
    def __init__(self, parent, sender: str, message: str, timestamp: str, is_own: bool = False, **kwargs):
        """
        Initialize chat bubble
        
        Args:
            parent: Parent widget
            sender: Message sender
            message: Message content
            timestamp: Message timestamp
            is_own: True if message is from current user
        """
        super().__init__(parent, **kwargs)
        
        self.sender = sender
        self.message = message
        self.timestamp = timestamp
        self.is_own = is_own
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create bubble UI"""
        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.X, padx=5, pady=2)
        
        # Bubble frame with styling
        bubble_frame = ttk.Frame(container, style="Bubble.TFrame")
        if self.is_own:
            bubble_frame.pack(side=tk.RIGHT, anchor=tk.E)
        else:
            bubble_frame.pack(side=tk.LEFT, anchor=tk.W)
        
        # Sender label
        sender_label = ttk.Label(bubble_frame, text=self.sender, font=("TkDefaultFont", 8, "bold"))
        sender_label.pack(anchor=tk.W if not self.is_own else tk.E, padx=5, pady=(5, 0))
        
        # Message text
        message_label = ttk.Label(bubble_frame, text=self.message, wraplength=300)
        message_label.pack(anchor=tk.W if not self.is_own else tk.E, padx=5, pady=(0, 5))
        
        # Timestamp
        time_label = ttk.Label(bubble_frame, text=self.timestamp, font=("TkDefaultFont", 7))
        time_label.pack(anchor=tk.W if not self.is_own else tk.E, padx=5, pady=(0, 5))


class MediaControlPanel(ttk.LabelFrame):
    """Media streaming control panel"""
    
    def __init__(self, parent, title: str = "Media Controls", **kwargs):
        """
        Initialize media control panel
        
        Args:
            parent: Parent widget
            title: Panel title
        """
        super().__init__(parent, text=title, **kwargs)
        
        self.audio_active = False
        self.video_active = False
        
        self.audio_callback: Optional[Callable] = None
        self.video_callback: Optional[Callable] = None
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create control UI"""
        # Audio controls
        audio_frame = ttk.Frame(self)
        audio_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(audio_frame, text="🎤").pack(side=tk.LEFT)
        self.audio_btn = ttk.Button(audio_frame, text="Start Audio", command=self._toggle_audio)
        self.audio_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        self.audio_status = ttk.Label(audio_frame, text="Off", foreground="red")
        self.audio_status.pack(side=tk.RIGHT)
        
        # Video controls
        video_frame = ttk.Frame(self)
        video_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(video_frame, text="📹").pack(side=tk.LEFT)
        self.video_btn = ttk.Button(video_frame, text="Start Video", command=self._toggle_video)
        self.video_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        self.video_status = ttk.Label(video_frame, text="Off", foreground="red")
        self.video_status.pack(side=tk.RIGHT)
        
        # Quality settings
        quality_frame = ttk.Frame(self)
        quality_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(quality_frame, text="Quality:").pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value="Medium")
        quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var,
                                   values=["Low", "Medium", "High"], state="readonly", width=8)
        quality_combo.pack(side=tk.LEFT, padx=(5, 0))
    
    def _toggle_audio(self) -> None:
        """Toggle audio streaming"""
        if self.audio_callback:
            self.audio_callback()
    
    def _toggle_video(self) -> None:
        """Toggle video streaming"""
        if self.video_callback:
            self.video_callback()
    
    def update_audio_status(self, active: bool) -> None:
        """
        Update audio status
        
        Args:
            active: True if audio is active
        """
        self.audio_active = active
        status_text = "On" if active else "Off"
        color = "green" if active else "red"
        
        self.audio_status.config(text=status_text, foreground=color)
        self.audio_btn.config(text="Stop Audio" if active else "Start Audio")
    
    def update_video_status(self, active: bool) -> None:
        """
        Update video status
        
        Args:
            active: True if video is active
        """
        self.video_active = active
        status_text = "On" if active else "Off"
        color = "green" if active else "red"
        
        self.video_status.config(text=status_text, foreground=color)
        self.video_btn.config(text="Stop Video" if active else "Start Video")
    
    def set_audio_callback(self, callback: Callable) -> None:
        """Set audio toggle callback"""
        self.audio_callback = callback
    
    def set_video_callback(self, callback: Callable) -> None:
        """Set video toggle callback"""
        self.video_callback = callback
    
    def get_quality(self) -> str:
        """Get selected quality setting"""
        return self.quality_var.get()


class FileTransferWidget(ttk.LabelFrame):
    """File transfer progress widget"""
    
    def __init__(self, parent, title: str = "File Transfer", **kwargs):
        """
        Initialize file transfer widget
        
        Args:
            parent: Parent widget
            title: Widget title
        """
        super().__init__(parent, text=title, **kwargs)
        
        self.current_transfers: Dict[str, Dict[str, Any]] = {}
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create transfer UI"""
        # Transfer list
        self.transfer_tree = ttk.Treeview(self, columns=("file", "progress", "status"), show="headings", height=5)
        self.transfer_tree.heading("file", text="File")
        self.transfer_tree.heading("progress", text="Progress")
        self.transfer_tree.heading("status", text="Status")
        
        self.transfer_tree.column("file", width=150)
        self.transfer_tree.column("progress", width=80)
        self.transfer_tree.column("status", width=80)
        
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.transfer_tree.yview)
        self.transfer_tree.configure(yscrollcommand=scrollbar.set)
        
        self.transfer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Button(btn_frame, text="Send File", command=self._send_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Cancel", command=self._cancel_transfer).pack(side=tk.LEFT)
    
    def _send_file(self) -> None:
        """Handle file send"""
        file_path = filedialog.askopenfilename(title="Select file to send")
        if file_path:
            # In real implementation, trigger file send
            transfer_id = f"send_{len(self.current_transfers)}"
            self.add_transfer(transfer_id, file_path, "sending")
    
    def _cancel_transfer(self) -> None:
        """Cancel selected transfer"""
        selection = self.transfer_tree.selection()
        if selection:
            transfer_id = selection[0]
            self.remove_transfer(transfer_id)
    
    def add_transfer(self, transfer_id: str, filename: str, status: str) -> None:
        """
        Add new file transfer
        
        Args:
            transfer_id: Unique transfer identifier
            filename: Name of file being transferred
            status: Transfer status
        """
        self.current_transfers[transfer_id] = {
            "filename": filename,
            "progress": 0,
            "status": status
        }
        
        self.transfer_tree.insert("", tk.END, iid=transfer_id,
                                values=(filename, "0%", status))
    
    def update_progress(self, transfer_id: str, progress: int) -> None:
        """
        Update transfer progress
        
        Args:
            transfer_id: Transfer identifier
            progress: Progress percentage (0-100)
        """
        if transfer_id in self.current_transfers:
            self.current_transfers[transfer_id]["progress"] = progress
            filename = self.current_transfers[transfer_id]["filename"]
            status = self.current_transfers[transfer_id]["status"]
            
            self.transfer_tree.item(transfer_id, values=(filename, f"{progress}%", status))
    
    def update_status(self, transfer_id: str, status: str) -> None:
        """
        Update transfer status
        
        Args:
            transfer_id: Transfer identifier
            status: New status
        """
        if transfer_id in self.current_transfers:
            self.current_transfers[transfer_id]["status"] = status
            filename = self.current_transfers[transfer_id]["filename"]
            progress = self.current_transfers[transfer_id]["progress"]
            
            self.transfer_tree.item(transfer_id, values=(filename, f"{progress}%", status))
    
    def remove_transfer(self, transfer_id: str) -> None:
        """
        Remove completed/cancelled transfer
        
        Args:
            transfer_id: Transfer identifier
        """
        if transfer_id in self.current_transfers:
            del self.current_transfers[transfer_id]
            self.transfer_tree.delete(transfer_id)


class SteganographyWidget(ttk.LabelFrame):
    """Steganography operations widget"""
    
    def __init__(self, parent, title: str = "Steganography", **kwargs):
        """
        Initialize steganography widget
        
        Args:
            parent: Parent widget
            title: Widget title
        """
        super().__init__(parent, text=title, **kwargs)
        
        self.hide_callback: Optional[Callable] = None
        self.reveal_callback: Optional[Callable] = None
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create stego UI"""
        # Hide message section
        hide_frame = ttk.LabelFrame(self, text="Hide Message")
        hide_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(hide_frame, text="Image:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.hide_image_entry = ttk.Entry(hide_frame, width=30)
        self.hide_image_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(hide_frame, text="Browse", command=self._browse_hide_image).grid(row=0, column=2, padx=5, pady=2)
        
        ttk.Label(hide_frame, text="Message:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.hide_message_entry = ttk.Entry(hide_frame, width=30)
        self.hide_message_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(hide_frame, text="Hide", command=self._hide_message).grid(row=2, column=0, columnspan=3, pady=5)
        
        # Reveal message section
        reveal_frame = ttk.LabelFrame(self, text="Reveal Message")
        reveal_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(reveal_frame, text="Image:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.reveal_image_entry = ttk.Entry(reveal_frame, width=30)
        self.reveal_image_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(reveal_frame, text="Browse", command=self._browse_reveal_image).grid(row=0, column=2, padx=5, pady=2)
        
        ttk.Button(reveal_frame, text="Reveal", command=self._reveal_message).grid(row=1, column=0, columnspan=3, pady=5)
        
        # Results display
        result_frame = ttk.LabelFrame(self, text="Results")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=6, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _browse_hide_image(self) -> None:
        """Browse for image to hide message in"""
        file_path = filedialog.askopenfilename(
            title="Select image for hiding",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if file_path:
            self.hide_image_entry.delete(0, tk.END)
            self.hide_image_entry.insert(0, file_path)
    
    def _browse_reveal_image(self) -> None:
        """Browse for image to reveal message from"""
        file_path = filedialog.askopenfilename(
            title="Select image for revealing",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if file_path:
            self.reveal_image_entry.delete(0, tk.END)
            self.reveal_image_entry.insert(0, file_path)
    
    def _hide_message(self) -> None:
        """Hide message in image"""
        image_path = self.hide_image_entry.get().strip()
        message = self.hide_message_entry.get().strip()
        
        if not image_path or not message:
            messagebox.showerror("Error", "Please select an image and enter a message")
            return
        
        if self.hide_callback:
            self.hide_callback(image_path, message)
    
    def _reveal_message(self) -> None:
        """Reveal message from image"""
        image_path = self.reveal_image_entry.get().strip()
        
        if not image_path:
            messagebox.showerror("Error", "Please select an image")
            return
        
        if self.reveal_callback:
            self.reveal_callback(image_path)
    
    def show_result(self, result: str) -> None:
        """
        Show operation result
        
        Args:
            result: Result message
        """
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)
    
    def set_hide_callback(self, callback: Callable) -> None:
        """Set hide message callback"""
        self.hide_callback = callback
    
    def set_reveal_callback(self, callback: Callable) -> None:
        """Set reveal message callback"""
        self.reveal_callback = callback


class ConnectionStatusWidget(ttk.Frame):
    """Connection status indicator widget"""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize connection status widget
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, **kwargs)
        
        self.connected = False
        self.peer_count = 0
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create status UI"""
        # Status indicator
        self.status_canvas = tk.Canvas(self, width=20, height=20)
        self.status_canvas.pack(side=tk.LEFT, padx=(0, 5))
        self._update_indicator()
        
        # Status text
        self.status_label = ttk.Label(self, text="Disconnected")
        self.status_label.pack(side=tk.LEFT)
        
        # Peer count
        self.peer_label = ttk.Label(self, text="Peers: 0")
        self.peer_label.pack(side=tk.RIGHT)
    
    def _update_indicator(self) -> None:
        """Update status indicator color"""
        self.status_canvas.delete("all")
        color = "green" if self.connected else "red"
        self.status_canvas.create_oval(2, 2, 18, 18, fill=color)
    
    def update_status(self, connected: bool, peer_count: int = 0) -> None:
        """
        Update connection status
        
        Args:
            connected: Connection status
            peer_count: Number of connected peers
        """
        self.connected = connected
        self.peer_count = peer_count
        
        self._update_indicator()
        
        status_text = "Connected" if connected else "Disconnected"
        self.status_label.config(text=status_text)
        self.peer_label.config(text=f"Peers: {peer_count}")


class SettingsDialog(tk.Toplevel):
    """Settings configuration dialog"""
    
    def __init__(self, parent, current_settings: Dict[str, Any], callback: Optional[Callable] = None):
        """
        Initialize settings dialog
        
        Args:
            parent: Parent window
            current_settings: Current settings dictionary
            callback: Callback for settings save
        """
        super().__init__(parent)
        
        self.title("Settings")
        self.geometry("400x500")
        self.resizable(False, False)
        
        self.current_settings = current_settings.copy()
        self.callback = callback
        
        self._create_ui()
        self._load_settings()
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
    
    def _create_ui(self) -> None:
        """Create settings UI"""
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General settings
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        self._create_general_settings(general_frame)
        
        # Network settings
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="Network")
        self._create_network_settings(network_frame)
        
        # Security settings
        security_frame = ttk.Frame(notebook)
        notebook.add(security_frame, text="Security")
        self._create_security_settings(security_frame)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Save", command=self._save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
    
    def _create_general_settings(self, parent) -> None:
        """Create general settings tab"""
        # Username
        ttk.Label(parent, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.username_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Theme
        ttk.Label(parent, text="Theme:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.theme_var = tk.StringVar()
        ttk.Combobox(parent, textvariable=self.theme_var, values=["Light", "Dark", "System"]).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Auto-connect
        self.auto_connect_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Auto-connect on startup", variable=self.auto_connect_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
    
    def _create_network_settings(self, parent) -> None:
        """Create network settings tab"""
        # Port
        ttk.Label(parent, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.port_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Max peers
        ttk.Label(parent, text="Max Peers:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_peers_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.max_peers_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Timeout
        ttk.Label(parent, text="Timeout (sec):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.timeout_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.timeout_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
    
    def _create_security_settings(self, parent) -> None:
        """Create security settings tab"""
        # Encryption level
        ttk.Label(parent, text="Encryption:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.encryption_var = tk.StringVar()
        ttk.Combobox(parent, textvariable=self.encryption_var, values=["AES-256", "ChaCha20"]).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Key rotation
        self.key_rotation_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable key rotation", variable=self.key_rotation_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Stego padding
        ttk.Label(parent, text="Stego Padding:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.stego_padding_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.stego_padding_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
    
    def _load_settings(self) -> None:
        """Load current settings into UI"""
        self.username_var.set(self.current_settings.get("username", ""))
        self.theme_var.set(self.current_settings.get("theme", "System"))
        self.auto_connect_var.set(self.current_settings.get("auto_connect", False))
        self.port_var.set(str(self.current_settings.get("port", 8080)))
        self.max_peers_var.set(str(self.current_settings.get("max_peers", 10)))
        self.timeout_var.set(str(self.current_settings.get("timeout", 30)))
        self.encryption_var.set(self.current_settings.get("encryption", "ChaCha20"))
        self.key_rotation_var.set(self.current_settings.get("key_rotation", True))
        self.stego_padding_var.set(str(self.current_settings.get("stego_padding", 1024)))
    
    def _save_settings(self) -> None:
        """Save settings and close dialog"""
        try:
            new_settings = {
                "username": self.username_var.get(),
                "theme": self.theme_var.get(),
                "auto_connect": self.auto_connect_var.get(),
                "port": int(self.port_var.get()),
                "max_peers": int(self.max_peers_var.get()),
                "timeout": int(self.timeout_var.get()),
                "encryption": self.encryption_var.get(),
                "key_rotation": self.key_rotation_var.get(),
                "stego_padding": int(self.stego_padding_var.get())
            }
            
            if self.callback:
                self.callback(new_settings)
            
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid setting value: {e}")


# Style configuration for custom widgets
def configure_styles() -> None:
    """Configure custom widget styles"""
    style = ttk.Style()
    
    # Chat bubble style
    style.configure("Bubble.TFrame", background="#E3F2FD", relief="raised", borderwidth=1)
    
    # Status indicators
    style.configure("Connected.TLabel", foreground="green")
    style.configure("Disconnected.TLabel", foreground="red")