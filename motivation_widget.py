import tkinter as tk
from tkinter import filedialog, Menu, messagebox
from PIL import Image, ImageTk
import os
import sys
import json
import shutil

import win32com.client

class ImageWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Motivation Widget")
        self.root.geometry("800x600")
        
        # Config file path
        self.config_file = os.path.join(os.path.expanduser("~"), "motivation_widget_config.json")
        
        # Initialize variables
        self.image_folder = ""
        self.images = []
        self.current_image_index = 0
        self.delay = 15000  # Default 15 seconds
        self.running = False
        self.current_photo = None  # Prevents garbage collection of the photo
        self.always_on_top = True
        self.position_locked = False
        self.dark_mode = False
        self.is_borderless = True
        self.in_startup = False
        self.timer_id = None
        self.resize_timer = None
        self.drag_data = {"x": 0, "y": 0}
        self.menu_showing = False
        
        # Load saved configuration and check startup status
        self.load_config()
        self.check_if_in_startup()
        
        # Apply window settings
        self.root.attributes("-topmost", self.always_on_top)
        
        # Create UI components
        self.create_ui()
        
        # Load images if we have a saved folder
        if self.image_folder:
            self.load_images()
            if self.images:
                self.running = True
                # Wait for window to render before showing the first image
                self.root.after(100, self.next_image)

    def create_ui(self):
        """Create all UI components including main frame, title bar and image display"""
        # Main container frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Custom title bar for borderless mode
        self.title_bar = tk.Frame(self.main_frame, height=22)
        self.title_bar.pack_propagate(0)  # Prevent auto-resizing
        
        self.title_label = tk.Label(self.title_bar, text="Motivation Widget", font=('Arial', 9))
        self.title_label.pack(side=tk.LEFT, padx=10)
        
        self.close_button = tk.Button(self.title_bar, text="✕", command=self.exit_app, 
                                    borderwidth=0, highlightthickness=0, font=('Arial', 9), width=3)
        self.close_button.pack(side=tk.RIGHT)
        
        self.minimize_button = tk.Button(self.title_bar, text="—", command=self.iconify_window, 
                                        borderwidth=0, highlightthickness=0, font=('Arial', 9), width=3)
        self.minimize_button.pack(side=tk.RIGHT)
        
        # Bind drag events to title bar
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.on_motion)
        
        # Image display area
        self.image_label = tk.Label(self.main_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Create right-click menu
        self.create_menus()
        
        # Bind right-click to show context menu
        self.root.bind("<Button-3>", self.show_menu)
        self.main_frame.bind("<Button-3>", self.show_menu)
        self.image_label.bind("<Button-3>", self.show_menu)
        
        # Apply theme and window style
        self.apply_theme()
        self.apply_window_style()
        
        # Update UI based on settings
        self.update_controls_visibility()

    def iconify_window(self):
        """Minimize the window. Uses a custom approach for borderless mode"""
        if self.is_borderless:
            # Hide main window
            self.root.wm_withdraw()
            
            # Create minimal icon window to represent the minimized app
            icon_window = tk.Toplevel(self.root)
            icon_window.title("Motivation Widget")
            icon_window.geometry("200x40+100+100")
            icon_window.attributes("-toolwindow", True)
            icon_window.resizable(False, False)
            
            # Add button to restore main window
            restore_btn = tk.Button(icon_window, text="Restore Motivation Widget", 
                                  command=lambda: self.restore_window(icon_window))
            restore_btn.pack(fill=tk.BOTH, expand=True)
            
            # Handle closing icon window
            icon_window.protocol("WM_DELETE_WINDOW", lambda: self.restore_window(icon_window))
        else:
            # Use standard minimize for windowed mode
            self.root.iconify()

    def restore_window(self, icon_window):
        """Restore the main window from minimized state"""
        icon_window.destroy()
        self.root.wm_deiconify()
        
        # Re-apply always on top if enabled
        if self.always_on_top:
            self.root.attributes("-topmost", True)

    def create_menus(self):
        """Create the right-click context menu with all settings options"""
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="Select Folder", command=self.select_folder)
        self.menu.add_command(label="Set Duration (seconds)", command=self.set_duration)
        
        # Toggle options with checkboxes
        self.always_on_top_var = tk.BooleanVar(value=self.always_on_top)
        self.menu.add_checkbutton(label="Always on Top", 
                                command=self.toggle_topmost, 
                                variable=self.always_on_top_var)
        
        self.position_locked_var = tk.BooleanVar(value=self.position_locked)
        self.menu.add_checkbutton(label="Lock Position", 
                                command=self.toggle_position_lock, 
                                variable=self.position_locked_var)
        
        self.dark_mode_var = tk.BooleanVar(value=self.dark_mode)
        self.menu.add_checkbutton(label="Dark Mode", 
                                command=self.toggle_theme, 
                                variable=self.dark_mode_var)
        
        self.borderless_var = tk.BooleanVar(value=self.is_borderless)
        self.menu.add_checkbutton(label="Borderless Mode", 
                                command=self.toggle_borderless, 
                                variable=self.borderless_var)
        
        self.startup_var = tk.BooleanVar(value=self.in_startup)
        self.menu.add_checkbutton(
            label="Run at Startup", 
            command=self.toggle_startup, 
            variable=self.startup_var)
        
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.exit_app)
    
    def check_if_in_startup(self):
        """Check if the application is set to run at Windows startup"""
        try:
            # Check if shortcut exists in Windows startup folder
            startup_folder = os.path.join(
                os.environ["APPDATA"], 
                r"Microsoft\Windows\Start Menu\Programs\Startup"
            )
            shortcut_path = os.path.join(startup_folder, "MotivationWidget.lnk")
            self.in_startup = os.path.exists(shortcut_path)
        except Exception:
            self.in_startup = False

    def load_config(self):
        """Load saved settings from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.image_folder = config.get('folder', '')
                    self.delay = config.get('delay', 15000)
                    self.always_on_top = config.get('always_on_top', True)
                    self.position_locked = config.get('position_locked', False)
                    self.dark_mode = config.get('dark_mode', False)
                    self.is_borderless = config.get('borderless', True)
                    geometry = config.get('geometry', '800x600')
                    self.root.geometry(geometry)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading configuration: {str(e)}")
    
    def save_config(self):
        """Save current settings to config file"""
        try:
            config = {
                'folder': self.image_folder,
                'delay': self.delay,
                'always_on_top': self.always_on_top,
                'position_locked': self.position_locked,
                'dark_mode': self.dark_mode,
                'borderless': self.is_borderless,
                'geometry': self.root.geometry()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {str(e)}")
    
    def apply_theme(self):
        """Apply light or dark theme to all UI elements"""
        if self.dark_mode:
            bg_color = "#222222"
            fg_color = "#FFFFFF"
            title_bg = "#333333"
            button_bg = "#444444"
        else:
            bg_color = "#FFFFFF"
            fg_color = "#000000"
            title_bg = "#F0F0F0"
            button_bg = "#E0E0E0"
        
        # Apply colors to UI elements
        self.root.configure(bg=bg_color)
        
        if hasattr(self, 'main_frame'):
            self.main_frame.configure(bg=bg_color)
            if hasattr(self, 'title_bar'):
                self.title_bar.configure(bg=title_bg)
                self.title_label.configure(bg=title_bg, fg=fg_color)
                self.close_button.configure(bg=button_bg, fg=fg_color, activebackground="#FF6B6B")
                self.minimize_button.configure(bg=button_bg, fg=fg_color, activebackground="#AAAAAA")
            self.image_label.configure(bg=bg_color)
            
    def apply_window_style(self):
        """Apply borderless or normal window style"""
        # Toggle borderless mode (no system window decorations)
        self.root.overrideredirect(self.is_borderless)
        
        # Show or hide custom title bar
        if self.is_borderless and hasattr(self, 'title_bar'):
            self.title_bar.pack(fill=tk.X, side=tk.TOP)
            self.title_bar.lift()
        elif hasattr(self, 'title_bar'):
            self.title_bar.pack_forget()
    
    def update_controls_visibility(self):
        """Update visibility of UI controls based on current settings"""
        if hasattr(self, 'title_bar'):
            if self.is_borderless:
                self.title_bar.pack(fill=tk.X, side=tk.TOP)
                self.title_bar.lift()
            else:
                self.title_bar.pack_forget()
    
    def start_move(self, event):
        """Start window drag operation"""
        if not self.position_locked:
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
    
    def on_motion(self, event):
        """Handle window dragging motion"""
        if not self.position_locked:
            deltax = event.x - self.drag_data["x"]
            deltay = event.y - self.drag_data["y"]
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
            
    def show_menu(self, event):
        """Display the right-click context menu"""
        # Prevent menu stacking by unposting first
        if self.menu_showing:
            self.menu.unpost()
        
        # Update checkboxes to match current settings
        self.always_on_top_var.set(self.always_on_top)
        self.position_locked_var.set(self.position_locked)
        self.dark_mode_var.set(self.dark_mode)
        self.borderless_var.set(self.is_borderless)
        self.startup_var.set(self.in_startup)
        
        # Show menu at cursor position
        self.menu.post(event.x_root, event.y_root)
        self.menu_showing = True
    
    def toggle_position_lock(self):
        """Toggle window position lock"""
        self.menu.unpost()
        self.menu_showing = False
        self.position_locked = self.position_locked_var.get()
        self.save_config()
        
    def toggle_topmost(self):
        """Toggle always-on-top window behavior"""
        self.menu.unpost()
        self.menu_showing = False
        self.always_on_top = self.always_on_top_var.get()
        self.root.attributes("-topmost", self.always_on_top)
        self.save_config()
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.menu.unpost()
        self.menu_showing = False
        self.dark_mode = self.dark_mode_var.get()
        self.apply_theme()
        self.save_config()
    
    def toggle_borderless(self):
        """Toggle between borderless and normal window style"""
        self.menu.unpost()
        self.menu_showing = False
        self.is_borderless = self.borderless_var.get()
        
        # Apply changes to window appearance
        self.apply_window_style()
        self.update_controls_visibility()
        
        # Force window redraw
        self.root.update_idletasks()
        self.save_config()
        
    def toggle_startup(self):
        """Toggle whether app runs at Windows startup"""
        # Hide menu
        if self.menu_showing:
            self.menu.unpost()
            self.menu_showing = False
        
        # Get new state from checkbox
        new_state = self.startup_var.get()
        
        # Add or remove from startup based on new state
        if new_state and not self.in_startup:
            self.add_to_startup()
        elif not new_state and self.in_startup:
            self.remove_from_startup()
    
    def select_folder(self):
        """Open folder selection dialog and load images"""
        # Hide menu
        if self.menu_showing:
            self.menu.unpost()
            self.menu_showing = False
        
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder = folder
            self.save_config()
            self.load_images()
            if self.images:
                self.running = True
                # Reset timer for image rotation
                if self.timer_id:
                    self.root.after_cancel(self.timer_id)
                self.show_image()
                self.timer_id = self.root.after(self.delay, self.next_image)
    
    def set_duration(self):
        """Open dialog to set image display duration"""
        # Hide menu first
        if self.menu_showing:
            self.menu.unpost()
            self.menu_showing = False
        
        # Use after() to ensure menu is fully hidden
        self.root.after(100, self._show_duration_dialog)

    def _show_duration_dialog(self):
        """Create and show duration setting dialog"""
        # Create modal dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Duration")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()  # Make dialog modal
        
        # Ensure dialog is always visible
        dialog.attributes("-topmost", True)
        
        # Position dialog near parent window
        dialog.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")
        
        # Apply current theme colors
        if self.dark_mode:
            dialog.configure(bg="#222222")
            fg_color = "#FFFFFF"
            bg_color = "#333333"
        else:
            dialog.configure(bg="#FFFFFF")
            fg_color = "#000000"
            bg_color = "#F0F0F0"
        
        # Create UI elements
        tk.Label(dialog, text="Seconds per image:", bg=dialog["bg"], fg=fg_color).pack(pady=(10, 5))
        
        # Entry with current value
        value = tk.StringVar(value=str(int(self.delay/1000)))
        entry = tk.Entry(dialog, textvariable=value, width=10)
        entry.pack(pady=5)
        
        # Instructions
        tk.Label(dialog, text="Press Enter to confirm", bg=dialog["bg"], fg=fg_color).pack(pady=(10, 0))
        tk.Label(dialog, text="Press ESC to cancel", bg=dialog["bg"], fg=fg_color).pack(pady=(0, 10))
        
        # Focus entry field and select text
        dialog.focus_force()
        dialog.after(100, lambda: (entry.focus_set(), entry.select_range(0, tk.END)))
        
        # Result storage
        result = [None]
        
        def on_enter(event=None):
            """Process entered value when Enter is pressed"""
            try:
                duration = int(value.get())
                if 1 <= duration <= 300:
                    result[0] = duration
                    dialog.destroy()
                else:
                    messagebox.showwarning("Invalid Input", "Please enter a number between 1 and 300.")
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter a valid number.")
        
        # Bind keyboard shortcuts
        dialog.bind("<Return>", on_enter)
        entry.bind("<Return>", on_enter)
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        # Process result if valid
        if result[0]:
            self.delay = result[0] * 1000
            self.save_config()
            # Reset timer if slideshow is running
            if self.running and self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = self.root.after(self.delay, self.next_image)

    def load_images(self):
        """Load all valid images from the selected folder"""
        self.images = []
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
        try:
            if not os.path.exists(self.image_folder):
                messagebox.showerror("Error", "Image folder does not exist.")
                return
                
            # Find all valid image files in the directory
            self.images = [
                entry.path for entry in os.scandir(self.image_folder)
                if entry.is_file() and os.path.splitext(entry.name.lower())[1] in valid_extensions
            ]
                    
            if not self.images:
                messagebox.showinfo("No Images", "No supported image files found in the selected folder.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading images: {str(e)}")
        
    def show_image(self):
        """Display the current image scaled to fit the window"""
        if not self.images:
            return
            
        try:
            image_path = self.images[self.current_image_index]
            img = Image.open(image_path)
            
            # Get current window dimensions
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # Use geometry string if window is not fully initialized
            if window_width <= 1 or window_height <= 1:
                geometry = self.root.geometry().split('+')[0]
                dimensions = geometry.split('x')
                window_width = max(int(dimensions[0]), 300)
                window_height = max(int(dimensions[1]), 200)
            
            # Account for title bar height in borderless mode
            if self.is_borderless and hasattr(self, 'title_bar'):
                title_height = self.title_bar.winfo_height()
                if title_height > 0:
                    window_height -= title_height
            
            # Scale image to fit window while preserving aspect ratio
            img_width, img_height = img.size
            ratio = min(window_width/max(img_width, 1), window_height/max(img_height, 1))
            new_width = max(int(img_width * ratio), 1)
            new_height = max(int(img_height * ratio), 1)
            
            # Resize and display the image
            if new_width > 0 and new_height > 0:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(img)
                self.current_photo = photo  # Save reference to prevent garbage collection
                self.image_label.config(image=photo)
                
                # Center image in window
                self.image_label.place(relx=0.5, rely=0.5, anchor='center')
            
        except Exception as e:
            print(f"Error showing image: {str(e)}")
        
    def next_image(self):
        """Move to the next image in the slideshow sequence"""
        if not self.images:
            return
            
        # Cycle to next image
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.show_image()
        
        # Schedule next image change
        self.timer_id = self.root.after(self.delay, self.next_image)
    
    def add_to_startup(self):
        """Add application to Windows startup"""
        try:
            # Get path to current executable
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = os.path.abspath(sys.argv[0])
                
            # Get Windows startup folder path
            startup_folder = os.path.join(
                os.environ["APPDATA"], 
                r"Microsoft\Windows\Start Menu\Programs\Startup"
            )
            
            # Create shortcut path
            shortcut_path = os.path.join(startup_folder, "MotivationWidget.lnk")
            
            # Create Windows shortcut
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.save()
            
            self.in_startup = True
            self.startup_var.set(True)
            messagebox.showinfo("Startup", "App added to startup.")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding to startup: {str(e)}")

    def remove_from_startup(self):
        """Remove application from Windows startup"""
        try:
            # Get Windows startup folder path
            startup_folder = os.path.join(
                os.environ["APPDATA"], 
                r"Microsoft\Windows\Start Menu\Programs\Startup"
            )
            
            # Shortcut path
            shortcut_path = os.path.join(startup_folder, "MotivationWidget.lnk")
            
            # Remove shortcut if it exists
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            
            self.in_startup = False
            self.startup_var.set(False)
            messagebox.showinfo("Startup", "App removed from startup.")
        except Exception as e:
            messagebox.showerror("Error", f"Error removing from startup: {str(e)}")
            
    def exit_app(self):
        """Save settings and exit the application"""
        # Hide menu if showing
        if self.menu_showing:
            self.menu.unpost()
            self.menu_showing = False
            
        self.save_config()
        self.root.quit()

# Create and run application
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageWidget(root)
    
    # Set minimum window size
    root.minsize(300, 200)
    
    # Handle window resize with debouncing to prevent lag
    def on_resize(event):
        # Only process actual size changes, not position changes
        if event.widget == root and (event.width != root.winfo_width() or event.height != root.winfo_height()):
            # Cancel any pending resize timer
            if app.resize_timer:
                root.after_cancel(app.resize_timer)
            
            # Schedule resize with delay to prevent multiple rapid calls
            app.resize_timer = root.after(100, app.show_image)
    
    root.bind("<Configure>", on_resize)
    
    # Ensure window is fully rendered before showing images
    root.update_idletasks()
    
    root.mainloop()