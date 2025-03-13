"""
XML uz PDF Konvertētājs ar Drag-and-Drop funkcionalitāti

Pirms lietošanas, lūdzu instalējiet tkinterdnd2 bibliotēku:
pip install tkinterdnd2

Ja nevar instalēt ar pip, lejupielādējiet no:
https://github.com/pmgagne/tkinterdnd2

Un novietojiet tkinterdnd2 mapi blakus šim skriptam.
"""

import os
import base64
import sys
import xml.etree.ElementTree as ET
import shutil
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
from datetime import datetime

APP_VERSION = "0.0.3v"  

class ConfigPage:
    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.bg_color = self.app.bg_color
        self.text_color = self.app.text_color
        self.primary_color = self.app.primary_color
        self.secondary_color = self.app.secondary_color
        
        # Create config variables
        self.input_folder = tk.StringVar(value=self.app.INPUT_FOLDER or "")
        self.log_file_folder = tk.StringVar(value=os.path.dirname(self.app.LOG_FILE) if self.app.LOG_FILE else "")
        
        self.create_widgets()
        
    def create_widgets(self):
        self.frame = ttk.Frame(self.parent, style="Main.TFrame")
        self.frame.pack(fill="both", expand=True)
        
        # Navigation buttons
        self.nav_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.nav_frame.pack(fill="x", pady=(0, 15))  # Reduced padding
        
        # Make navigation buttons consistent size
        button_width = 14  # Slightly smaller
        button_pad = 4  # Reduced padding
        
        self.home_button = ttk.Button(self.nav_frame, 
                                     text="Sākums", 
                                     command=self.app.show_main_page,
                                     style="TButton",
                                     width=button_width)
        self.home_button.pack(side="left", padx=button_pad, pady=button_pad)
        
        self.settings_button = ttk.Button(self.nav_frame, 
                                        text="Iestatījumi", 
                                        command=self.app.show_config_page,
                                        style="Primary.TButton",
                                        width=button_width)
        self.settings_button.pack(side="left", padx=button_pad, pady=button_pad)
        
        # Add title and icon for consistency with main page
        self.header_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.header_frame.pack(fill="x", pady=(0, 15))  # Reduced padding
        
        self.title_frame = ttk.Frame(self.header_frame, style="Main.TFrame")
        self.title_frame.pack(side="left", fill="x")
        
        self.leaf_icon = self.app.create_leaf_icon(self.title_frame)
        self.leaf_icon.pack(side="left", padx=(0, 10))
        
        self.title_label = ttk.Label(self.title_frame, 
                                    text="XML uz PDF Konvertētājs", 
                                    style="Title.TLabel")
        self.title_label.pack(side="left")
        
        self.version_label = ttk.Label(self.header_frame,
                                      text=self.app.VERSION,
                                      style="Version.TLabel")
        self.version_label.pack(side="right", padx=(0, 5))
        
        self.separator = ttk.Separator(self.frame, orient="horizontal")
        self.separator.pack(fill="x", pady=(0, 15))  # Reduced padding
        
        # Main content
        self.content = ttk.Frame(self.frame, padding="15", style="Main.TFrame")  # Reduced padding
        self.content.pack(fill="both", expand=True, padx=15, pady=0)  # Reduced padding
        
        # Settings title
        self.settings_title = ttk.Label(self.content, 
                                    text="Iestatījumi", 
                                    style="Subtitle.TLabel")
        self.settings_title.pack(anchor="w", pady=(0, 15))  # Reduced padding
        
        # Input folder is now optional
        self.create_folder_selection_row("XML Failu mape (neobligāts):", self.input_folder)
        
        # Log file folder
        self.create_folder_selection_row("Žurnāla failu mape:", self.log_file_folder)
        
        # Log file settings frame
        log_settings_frame = ttk.Frame(self.content, style="Main.TFrame")
        log_settings_frame.pack(fill="x", pady=(5, 10))  # Reduced padding
        
        log_settings_label = ttk.Label(log_settings_frame, 
                                     text="Žurnāla failu iestatījumi:", 
                                     style="TLabel", 
                                     font=("Segoe UI", 10, "bold"))  # Smaller font
        log_settings_label.pack(anchor="w", pady=(0, 8))  # Reduced padding
        
        # Max log file size setting
        self.max_log_size_var = tk.StringVar(value=str(self.app.MAX_LOG_SIZE))
        max_size_frame = ttk.Frame(log_settings_frame, style="Main.TFrame")
        max_size_frame.pack(fill="x", pady=(0, 4))  # Reduced padding
        
        max_size_label = ttk.Label(max_size_frame, 
                                  text="Maksimālais žurnāla faila izmērs (MB):", 
                                  style="TLabel")
        max_size_label.pack(side="left", padx=(0, 8))  # Reduced padding
        
        max_size_entry = ttk.Entry(max_size_frame, 
                                 textvariable=self.max_log_size_var, 
                                 width=8)  # Smaller width
        max_size_entry.pack(side="left")
        
        # Max record count setting
        self.max_records_var = tk.StringVar(value=str(self.app.MAX_LOG_RECORDS))
        max_records_frame = ttk.Frame(log_settings_frame, style="Main.TFrame")
        max_records_frame.pack(fill="x", pady=(0, 4))  # Reduced padding
        
        max_records_label = ttk.Label(max_records_frame, 
                                    text="Maksimālais ierakstu skaits žurnāla failā:", 
                                    style="TLabel")
        max_records_label.pack(side="left", padx=(0, 8))  # Reduced padding
        
        max_records_entry = ttk.Entry(max_records_frame, 
                                    textvariable=self.max_records_var, 
                                    width=8)  # Smaller width
        max_records_entry.pack(side="left")
        
        # Log success checkbox
        log_success_frame = ttk.Frame(log_settings_frame, style="Main.TFrame")
        log_success_frame.pack(fill="x", pady=(4, 0))  # Reduced padding
        
        self.log_success_var = tk.BooleanVar(value=self.app.LOG_SUCCESS)
        log_success_checkbox = ttk.Checkbutton(log_success_frame,
                                             text="Reģistrēt veiksmīgās konversijas žurnālā",
                                             variable=self.log_success_var,
                                             style="TCheckbutton")
        log_success_checkbox.pack(anchor="w")
        
        # Buttons
        self.button_frame = ttk.Frame(self.content, style="Main.TFrame")
        self.button_frame.pack(fill="x", pady=(20, 0))  # Reduced padding
        
        self.cancel_button = ttk.Button(self.button_frame, 
                                      text="Atcelt", 
                                      command=self.app.show_main_page,
                                      style="TButton",
                                      width=button_width)
        self.cancel_button.pack(side="right", padx=(8, 0))  # Reduced padding
        
        self.save_button = ttk.Button(self.button_frame, 
                                     text="Saglabāt", 
                                     command=self.save_config,
                                     style="Primary.TButton",
                                     width=button_width)
        self.save_button.pack(side="right")
        
        # Add green progress frame at the bottom like in the main page
        self.progress_frame = tk.Frame(self.frame, bg=self.secondary_color, height=8)  # Smaller height
        self.progress_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        # Add status label above the progress frame
        self.status_label = tk.Label(self.frame, 
                                   text="Konfigurējiet iestatījumus un nospiediet Saglabāt", 
                                   font=("Segoe UI", 10),  # Smaller font
                                   bg=self.bg_color, 
                                   fg=self.text_color)
        self.status_label.pack(side="bottom", anchor="w", pady=(8, 0))  # Reduced padding
    
    def create_folder_selection_row(self, label_text, string_var):
        frame = ttk.Frame(self.content, style="Main.TFrame")
        frame.pack(fill="x", pady=(0, 10))  # Reduced padding
        
        label = ttk.Label(frame, text=label_text, style="TLabel")
        label.pack(anchor="w", pady=(0, 4))  # Reduced padding
        
        selection_frame = ttk.Frame(frame, style="Main.TFrame")
        selection_frame.pack(fill="x")
        
        entry = ttk.Entry(selection_frame, textvariable=string_var, width=45)  # Reduced width
        entry.pack(side="left", fill="x", expand=True)
        
        button = ttk.Button(selection_frame, 
                           text="Izvēlēties", 
                           command=lambda sv=string_var: self.browse_folder(sv),
                           style="TButton")
        button.pack(side="right", padx=(8, 0))  # Reduced padding
    
    def browse_folder(self, string_var):
        folder = filedialog.askdirectory(title="Izvēlieties mapi")
        if folder:
            string_var.set(folder)
    
    def save_config(self):
        # Validate log settings
        try:
            max_log_size = float(self.max_log_size_var.get())
            if max_log_size <= 0:
                raise ValueError("Izmēram jābūt pozitīvam skaitlim")
        except ValueError:
            messagebox.showwarning("Brīdinājums", "Lūdzu ievadiet derīgu maksimālo žurnāla izmēru!")
            return
            
        try:
            max_records = int(self.max_records_var.get())
            if max_records <= 0:
                raise ValueError("Ierakstu skaitam jābūt pozitīvam skaitlim")
        except ValueError:
            messagebox.showwarning("Brīdinājums", "Lūdzu ievadiet derīgu maksimālo ierakstu skaitu!")
            return
        
        # Apply settings to main app
        self.app.INPUT_FOLDER = self.input_folder.get()
        log_folder = self.log_file_folder.get() or os.path.expanduser("~")
        self.app.LOG_FILE = os.path.join(log_folder, "error_log.txt")
        self.app.MAX_LOG_SIZE = max_log_size
        self.app.MAX_LOG_RECORDS = max_records
        self.app.LOG_SUCCESS = self.log_success_var.get()
        
        # Create log directory if needed
        if log_folder:
            os.makedirs(log_folder, exist_ok=True)
        
        # Save configuration to file for future startups
        self.app.save_config_to_file()
        
        # Update main application
        self.app.main_page.config_label.config(text=self.app.INPUT_FOLDER or "Nav izvēlēta mape")
        self.app.main_page.status_label.config(text="Iestatījumi veiksmīgi saglabāti", fg=self.app.success_color)
        
        # Update status label in the settings page
        self.status_label.config(text="Iestatījumi veiksmīgi saglabāti", fg=self.app.success_color)
        
        # Switch to main page
        self.app.show_main_page()


class MainPage:
    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.bg_color = self.app.bg_color
        self.text_color = self.app.text_color
        self.primary_color = self.app.primary_color
        self.secondary_color = self.app.secondary_color
        self.success_color = self.app.success_color
        self.error_color = self.app.error_color
        
        self.selected_file = tk.StringVar()  # Track the selected file
        self.create_widgets()
        
        # Set up drag and drop functionality
        if self.app.has_dnd:
            self.setup_drag_drop()
        
    def create_widgets(self):
        self.frame = ttk.Frame(self.parent, style="Main.TFrame")
        self.frame.pack(fill="both", expand=True)
        
        # Navigation buttons
        self.nav_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.nav_frame.pack(fill="x", pady=(0, 15))  # Reduced padding
        
        # Make navigation buttons consistent size
        button_width = 14  # Slightly smaller
        button_pad = 4  # Reduced padding
        
        self.home_button = ttk.Button(self.nav_frame, 
                                     text="Sākums", 
                                     command=self.app.show_main_page,
                                     style="Primary.TButton",  # Active button
                                     width=button_width)
        self.home_button.pack(side="left", padx=button_pad, pady=button_pad)
        
        self.settings_button = ttk.Button(self.nav_frame, 
                                        text="Iestatījumi", 
                                        command=self.app.show_config_page,
                                        style="TButton",
                                        width=button_width)
        self.settings_button.pack(side="left", padx=button_pad, pady=button_pad)
        
        # Title and icon
        self.header_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.header_frame.pack(fill="x", pady=(0, 15))  # Reduced padding
        
        self.title_frame = ttk.Frame(self.header_frame, style="Main.TFrame")
        self.title_frame.pack(side="left", fill="x")
        
        self.leaf_icon = self.app.create_leaf_icon(self.title_frame)
        self.leaf_icon.pack(side="left", padx=(0, 10))
        
        self.title_label = ttk.Label(self.title_frame, 
                                    text="XML uz PDF Konvertētājs", 
                                    style="Title.TLabel")
        self.title_label.pack(side="left")
        
        self.version_label = ttk.Label(self.header_frame,
                                      text=self.app.VERSION,
                                      style="Version.TLabel")
        self.version_label.pack(side="right", padx=(0, 5))
        
        self.separator = ttk.Separator(self.frame, orient="horizontal")
        self.separator.pack(fill="x", pady=(0, 15))  # Reduced padding
        
        # Main content
        self.content_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=0)  # Reduced padding
        
        # Current folder section
        self.folder_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.folder_frame.pack(fill="x", pady=(0, 12))  # Reduced padding
        
        self.folder_label = ttk.Label(self.folder_frame, 
                                     text="Pašreizējā XML failu mape:", 
                                     style="TLabel")
        self.folder_label.pack(anchor="w", pady=(0, 4))  # Reduced padding
        
        self.folder_display_frame = ttk.Frame(self.folder_frame, style="Main.TFrame")
        self.folder_display_frame.pack(fill="x")
        
        self.config_label = tk.Label(self.folder_display_frame, 
                                   text="Nav izvēlēta mape", 
                                   font=("Segoe UI", 10),  # Smaller font
                                   bg="white", 
                                   fg=self.text_color,
                                   anchor="w",
                                   padx=8,  # Reduced padding
                                   pady=6,  # Reduced padding
                                   relief="groove",
                                   bd=1)
        self.config_label.pack(side="left", fill="x", expand=True)
        
        # File selection section - Changed to use browse button instead of dropdown
        self.file_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.file_frame.pack(fill="x", pady=(4, 8))  # Reduced padding
        
        self.file_label = ttk.Label(self.file_frame, 
                                   text="XML Fails:", 
                                   style="TLabel")
        self.file_label.pack(anchor="w", pady=(0, 4))  # Reduced padding
        
        # Add drop zone for drag and drop
        self.drop_frame = ttk.Frame(self.file_frame, style="DropZone.TFrame", cursor="hand2")
        self.drop_frame.pack(fill="x", pady=(0, 5))
        
        self.drop_label = ttk.Label(self.drop_frame, 
                                 text="Velciet XML failu šeit vai izvēlieties to", 
                                 style="DropZone.TLabel",
                                 anchor="center")
        self.drop_label.pack(fill="both", expand=True, pady=15)
        
        # Standard file selection controls
        self.file_selection_frame = ttk.Frame(self.file_frame, style="Main.TFrame")
        self.file_selection_frame.pack(fill="x")
        
        self.file_entry = ttk.Entry(self.file_selection_frame, 
                                  textvariable=self.selected_file,
                                  width=45,  # Reduced width
                                  state="readonly")
        self.file_entry.pack(side="left", fill="x", expand=True)
        
        self.browse_button = ttk.Button(self.file_selection_frame,
                                      text="Izvēlēties",
                                      command=self.browse_file,
                                      style="TButton")
        self.browse_button.pack(side="right", padx=(8, 0))  # Reduced padding
        
        self.description_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.description_frame.pack(fill="x", pady=(4, 15))  # Reduced padding
        
        self.description_label = tk.Label(self.description_frame, 
                                        text="Izvēlieties XML failu un nospiediet 'Sākt', lai konvertētu uz PDF", 
                                        font=("Segoe UI", 10, "italic"),  # Smaller font
                                        bg=self.bg_color, 
                                        fg=self.text_color)
        self.description_label.pack(anchor="w")
        
        # Action button
        self.button_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.button_frame.pack(fill="x", pady=8)  # Reduced padding
        
        self.start_button = ttk.Button(self.button_frame, 
                                      text="Sākt", 
                                      command=self.app.process_selected_file,
                                      style="Primary.TButton",
                                      width=button_width)
        self.start_button.pack(side="right")
        
        # Status section
        self.status_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.status_frame.pack(fill="x", pady=(15, 0))  # Reduced padding
        
        self.file_count_label = tk.Label(self.status_frame,
                                      text="Izmantojiet drag-and-drop vai izvēlieties XML failu",
                                      font=("Segoe UI", 10),  # Smaller font
                                      bg=self.bg_color,
                                      fg=self.text_color)
        self.file_count_label.pack(anchor="w", pady=(0, 8))  # Reduced padding
        
        self.progress_frame = tk.Frame(self.frame, bg=self.secondary_color, height=8)  # Smaller height
        self.progress_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        self.status_label = tk.Label(self.frame, 
                                   text="Gatavs konvertēšanai", 
                                   font=("Segoe UI", 10),  # Smaller font
                                   bg=self.bg_color, 
                                   fg=self.text_color)
        self.status_label.pack(side="bottom", anchor="w", pady=(8, 0))  # Reduced padding
    
    def setup_drag_drop(self):
        try:
            self.drop_frame.drop_target_register("DND_Files")
            self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)
            
            # Change appearance on drag enter/leave
            self.drop_frame.bind('<Enter>', lambda e: self.drop_frame.configure(style="DropZoneHover.TFrame"))
            self.drop_frame.bind('<Leave>', lambda e: self.drop_frame.configure(style="DropZone.TFrame"))
            
            # Make the label also a drop target
            self.drop_label.drop_target_register("DND_Files")
            self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        except Exception as e:
            print(f"Error setting up drag and drop: {str(e)}")
    
    def handle_drop(self, event):
        # Reset drop zone appearance
        self.drop_frame.configure(style="DropZone.TFrame")
        
        # Get the dropped file path
        file_path = event.data
        
        # Handle the file
        self.process_selected_file_path(file_path)
    
    def browse_file(self):
        initial_dir = self.app.INPUT_FOLDER if self.app.INPUT_FOLDER and os.path.exists(self.app.INPUT_FOLDER) else os.path.expanduser("~")
        file_path = filedialog.askopenfilename(
            title="Izvēlieties XML failu",
            initialdir=initial_dir,
            filetypes=[("XML files", "*.xml")]
        )
        
        if file_path:
            self.process_selected_file_path(file_path)
    
    def process_selected_file_path(self, file_path):
        if not file_path:
            return
            
        if not file_path.lower().endswith('.xml'):
            messagebox.showwarning("Brīdinājums", "Lūdzu izvēlieties XML failu!")
            return
            
        # Get just the filename without the path
        filename = os.path.basename(file_path)
        
        # Store the full path instead of just the filename
        self.selected_file.set(file_path)
        self.status_label.config(text=f"Izvēlēts fails: {filename}", fg=self.text_color)


class XMLToPDFConverter:
    def __init__(self):
        self.VERSION = APP_VERSION
        self.INPUT_FOLDER = ""
        self.LOG_FILE = ""
        self.MAX_LOG_SIZE = 1  # Default max log file size in MB
        self.MAX_LOG_RECORDS = 100  # Default max number of records in log file
        self.LOG_SUCCESS = False  # Whether to log successful conversions
        self.log_record_count = 0  # Current record count in log file
        self.has_dnd = False  # Whether drag and drop is available
        
        self.setup_gui()
        
    def setup_gui(self):
        # Add tkinterdnd2 to path if it exists as a module next to our script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tkdnd_dir = os.path.join(script_dir, "tkinterdnd2")
        if os.path.exists(tkdnd_dir):
            sys.path.append(script_dir)
        
        # Import tkinterdnd2 for drag and drop functionality
        try:
            import tkinterdnd2
            self.root = tkinterdnd2.Tk()
            self.has_dnd = True
        except ImportError:
            self.root = tk.Tk()
            self.has_dnd = False
            print("tkinterdnd2 not available, drag and drop functionality disabled")
        
        self.root.title("XML uz PDF Konvertētājs")
        
        win_width, win_height = 700, 820  # Window size as requested
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_cord = int((screen_width / 2) - (win_width / 2))
        y_cord = int((screen_height / 2) - (win_height / 2))
        self.root.geometry(f"{win_width}x{win_height}+{x_cord}+{y_cord}")
        
        self.primary_color = "#2e7d32"
        self.secondary_color = "#4caf50"
        self.accent_color = "#81c784"
        self.bg_color = "#f1f8e9"
        self.success_color = "#2e7d32"
        self.error_color = "#c62828"
        self.text_color = "#33691e"
        
        self.root.configure(bg=self.bg_color)
        self.setup_styles()
        
        self.main_container = ttk.Frame(self.root, padding="25 15 25 15", style="Main.TFrame")  # Reduced padding
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)  # Reduced padding
        
        # Create pages but only show main page initially
        self.main_page = MainPage(self.main_container, self)
        self.config_page = ConfigPage(self.main_container, self)
        
        # Initially hide config page
        self.config_page.frame.pack_forget()
        
    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        
        style.configure("Main.TFrame", background=self.bg_color)
        
        # Configure drop zone styles
        style.configure("DropZone.TFrame", 
                       background="#e8f5e9",
                       borderwidth=2,
                       relief="groove")
                       
        style.configure("DropZoneHover.TFrame", 
                       background="#c8e6c9",
                       borderwidth=2,
                       relief="groove")
                       
        style.configure("DropZone.TLabel", 
                       font=("Segoe UI", 11, "italic"),
                       foreground=self.text_color,
                       background="#e8f5e9")
        
        style.configure("Title.TLabel", 
                        font=("Segoe UI", 18, "bold"),  # Smaller font
                        foreground=self.primary_color, 
                        background=self.bg_color)
        
        style.configure("Subtitle.TLabel", 
                        font=("Segoe UI", 14, "bold"),  # Smaller font
                        foreground=self.primary_color, 
                        background=self.bg_color)
        
        style.configure("TLabel", 
                        font=("Segoe UI", 10),  # Smaller font
                        foreground=self.text_color, 
                        background=self.bg_color)
        
        style.configure("Status.TLabel", 
                        font=("Segoe UI", 10),  # Smaller font
                        foreground=self.success_color, 
                        background=self.bg_color)
        
        style.configure("Version.TLabel",
                        font=("Segoe UI", 9),
                        foreground="#777777",
                        background=self.bg_color)
        
        style.configure("TButton", 
                        font=("Segoe UI", 10),  # Smaller font
                        background=self.secondary_color,
                        foreground="white")
        
        style.map("TButton",
                  background=[("active", self.primary_color), 
                             ("pressed", "#1b5e20")],
                  relief=[("pressed", "flat"), ("!pressed", "flat")])
        
        style.configure("Primary.TButton", 
                        font=("Segoe UI", 11, "bold"),  # Smaller font
                        background=self.secondary_color,
                        foreground="white")
        
        style.map("Primary.TButton",
                  background=[("active", self.primary_color), 
                             ("pressed", "#1b5e20")])
        
        style.configure("TEntry", 
                        font=("Segoe UI", 10),  # Smaller font
                        foreground=self.text_color)
        
        style.configure("TCheckbutton",
                        font=("Segoe UI", 10),  # Smaller font
                        foreground=self.text_color,
                        background=self.bg_color)
        
        style.map("TCheckbutton",
                   background=[("active", self.bg_color)])
        
    def create_leaf_icon(self, parent):
        canvas = tk.Canvas(parent, width=25, height=25, bg=self.bg_color, highlightthickness=0)  # Smaller canvas
        
        canvas.create_oval(4, 4, 21, 21, fill=self.secondary_color, outline=self.primary_color)  # Smaller oval
        canvas.create_arc(7, 7, 18, 18, start=45, extent=180, fill=self.accent_color, outline="")  # Smaller arc
        canvas.create_line(12.5, 21, 12.5, 13, fill=self.primary_color, width=1.5)  # Thinner line
        
        return canvas
    
    def show_main_page(self):
        self.config_page.frame.pack_forget()
        self.main_page.frame.pack(fill="both", expand=True)
        # Update button states for visual feedback
        self.main_page.home_button.configure(style="Primary.TButton")
        self.main_page.settings_button.configure(style="TButton")
    
    def show_config_page(self):
        self.main_page.frame.pack_forget()
        self.config_page.frame.pack(fill="both", expand=True)
        # Update button states for visual feedback
        self.config_page.home_button.configure(style="TButton")
        self.config_page.settings_button.configure(style="Primary.TButton")
        
    def process_selected_file(self):
        selected_file_path = self.main_page.selected_file.get()
        if not selected_file_path:
            messagebox.showwarning("Brīdinājums", "Lūdzu izvēlieties XML failu!")
            self.main_page.status_label.config(text="Nav izvēlēts fails", fg=self.error_color)
            return
        
        # Get just the filename without the path
        selected_filename = os.path.basename(selected_file_path)
        
        self.main_page.status_label.config(text=f"Apstrādā {selected_filename}...", fg=self.text_color)
        self.root.update()
        
        # Use the full path directly
        xml_file_path = selected_file_path
        
        # Check if file exists
        if not os.path.exists(xml_file_path):
            messagebox.showwarning("Brīdinājums", f"Fails {selected_filename} vairs neeksistē!")
            self.main_page.status_label.config(text="Fails nav atrasts", fg=self.error_color)
            return
        
        # Create output directory if it doesn't exist
        pdf_output_dir = os.path.dirname(xml_file_path)
        pdf_output_path = os.path.join(pdf_output_dir, selected_filename.replace(".xml", ".pdf"))
        
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            namespaces = {
                "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
                "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            }
            
            binary_object = root.find(".//cbc:EmbeddedDocumentBinaryObject", namespaces)
            if binary_object is not None:
                base64_data = binary_object.text.strip()
                pdf_data = base64.b64decode(base64_data)
                
                with open(pdf_output_path, "wb") as pdf_file:
                    pdf_file.write(pdf_data)
                
                # Don't move the XML file, just keep it where it is
                
                # Open the generated PDF
                if os.name == "nt":
                    os.startfile(pdf_output_path)
                else:
                    subprocess.run(["xdg-open", pdf_output_path])
                
                self.main_page.status_label.config(text=f"PDF izveidots veiksmīgi: {os.path.basename(pdf_output_path)}", fg=self.success_color)
                messagebox.showinfo("Veiksmīgi", f"PDF izveidots: {pdf_output_path}")
                
                # Log successful conversion if enabled
                self.log_success(selected_filename)
            else:
                raise ValueError("cbc:EmbeddedDocumentBinaryObject mezgls netika atrasts")
        except Exception as e:
            # Don't move the file to an error folder, just log the error
            
            # Log the error in the structured format
            self.log_error(selected_filename, str(e))
            
            self.main_page.status_label.config(text=f"Kļūda apstrādājot {selected_filename}", fg=self.error_color)
            messagebox.showerror("Kļūda", f"Kļūda apstrādājot failu: {selected_filename}\n\nLūdzu pārbaudiet kļūdu žurnālu papildu informācijai.")
        
        # Clear selected file after processing
        self.main_page.selected_file.set("")
        
    def log_error(self, file_name, error_message):
        try:
            # If LOG_FILE is not set, use a default location
            if not self.LOG_FILE:
                self.LOG_FILE = os.path.join(os.path.expanduser("~"), "xml2pdf_error_log.txt")
                
            # Make sure the log directory exists
            log_dir = os.path.dirname(self.LOG_FILE)
            os.makedirs(log_dir, exist_ok=True)
            
            # Check if we need to create a new log file
            new_log_file = self.LOG_FILE
            
            if os.path.exists(self.LOG_FILE):
                # Check file size
                file_size_mb = os.path.getsize(self.LOG_FILE) / (1024 * 1024)  # Convert to MB
                
                # Count records in file
                if self.log_record_count == 0:  # Only count if we haven't already
                    with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
                        self.log_record_count = sum(1 for line in f if line.startswith("Ielādes datums:"))
                
                # If either limit is exceeded, create a new log file
                if file_size_mb >= self.MAX_LOG_SIZE or self.log_record_count >= self.MAX_LOG_RECORDS:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_dir = os.path.dirname(self.LOG_FILE)
                    log_name = os.path.basename(self.LOG_FILE)
                    base_name, ext = os.path.splitext(log_name)
                    new_log_file = os.path.join(log_dir, f"{base_name}_{timestamp}{ext}")
                    self.log_record_count = 0  # Reset count for new file
            
            # Format the error log entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = (
                f"Ielādes datums: {timestamp}\n"
                f"Statuss: KĻŪDA\n"
                f"Faila nosaukums: {file_name}\n"
                f"KĻŪDAS APRAKSTS/PIEZĪMES: {error_message}\n"
                f"{'='*50}\n\n"
            )
            
            # Write to log file
            with open(new_log_file, "a", encoding="utf-8") as log:
                log.write(log_entry)
            
            # Update record count
            self.log_record_count += 1
            
            # If we created a new file, update the LOG_FILE path
            if new_log_file != self.LOG_FILE:
                self.LOG_FILE = new_log_file
        except Exception as e:
            # Fail silently but show error in console for debugging
            print(f"Error writing to log file: {str(e)}")
    
    def log_success(self, file_name):
        # Only log if LOG_SUCCESS is enabled
        if not self.LOG_SUCCESS:
            return
        
        try:
            # If LOG_FILE is not set, use a default location
            if not self.LOG_FILE:
                self.LOG_FILE = os.path.join(os.path.expanduser("~"), "xml2pdf_error_log.txt")
            
            # Make sure the log directory exists
            log_dir = os.path.dirname(self.LOG_FILE)
            os.makedirs(log_dir, exist_ok=True)
                
            # Check if we need to create a new log file (same as in log_error)
            new_log_file = self.LOG_FILE
            
            if os.path.exists(self.LOG_FILE):
                file_size_mb = os.path.getsize(self.LOG_FILE) / (1024 * 1024)
                
                if self.log_record_count == 0:
                    with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
                        self.log_record_count = sum(1 for line in f if line.startswith("Ielādes datums:"))
                
                if file_size_mb >= self.MAX_LOG_SIZE or self.log_record_count >= self.MAX_LOG_RECORDS:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_dir = os.path.dirname(self.LOG_FILE)
                    log_name = os.path.basename(self.LOG_FILE)
                    base_name, ext = os.path.splitext(log_name)
                    new_log_file = os.path.join(log_dir, f"{base_name}_{timestamp}{ext}")
                    self.log_record_count = 0
            
            # Format the success log entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = (
                f"Ielādes datums: {timestamp}\n"
                f"Statuss: VEIKSMĪGI\n"
                f"Faila nosaukums: {file_name}\n"
                f"KĻŪDAS APRAKSTS/PIEZĪMES: -\n"
                f"{'='*50}\n\n"
            )
            
            # Write to log file
            with open(new_log_file, "a", encoding="utf-8") as log:
                log.write(log_entry)
            
            # Update record count
            self.log_record_count += 1
            
            # If we created a new file, update the LOG_FILE path
            if new_log_file != self.LOG_FILE:
                self.LOG_FILE = new_log_file
        except Exception as e:
            # Fail silently but show error in console for debugging
            print(f"Error writing to success log: {str(e)}")
    
    def update_file_list(self):
        # We don't need to count files anymore since we're using drag and drop
        self.main_page.file_count_label.config(text="Izmantojiet drag-and-drop vai izvēlieties XML failu")
        self.main_page.status_label.config(text="Gatavs konvertēšanai", fg=self.success_color)
    
    def save_config_to_file(self):
        # Save current configuration to a file for next startup
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt"), "w") as f:
                f.write(f"INPUT_FOLDER={self.INPUT_FOLDER}\n")
        except Exception as e:
            print(f"Error saving config: {str(e)}")
    
    def run(self):
        # Add tkinterdnd2 to path if it exists as a module next to our script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tkdnd_dir = os.path.join(script_dir, "tkinterdnd2")
        if os.path.exists(tkdnd_dir):
            sys.path.append(script_dir)
        
        # Apply initial configuration
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")):
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt"), "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            if key == "INPUT_FOLDER":
                                self.INPUT_FOLDER = value
                                
                                # Set a default log file in user's home directory
                                if not self.LOG_FILE:
                                    self.LOG_FILE = os.path.join(os.path.expanduser("~"), "xml2pdf_error_log.txt")
                                
                                # Update UI
                                if os.path.exists(value):
                                    self.main_page.config_label.config(text=self.INPUT_FOLDER)
                                else:
                                    self.main_page.config_label.config(text="Nav izvēlēta mape vai tā neeksistē")
                                    
                                self.update_file_list()
                                self.main_page.status_label.config(text="Gatavs darbam", fg=self.success_color)
            except Exception as e:
                print(f"Error loading config: {str(e)}")
        
        self.root.mainloop()

if __name__ == "__main__":
    app = XMLToPDFConverter()
    app.run()