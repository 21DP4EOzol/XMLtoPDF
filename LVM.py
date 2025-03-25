import os
import base64
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
        self.processed_folder = tk.StringVar(value=self.app.PROCESSED_FOLDER or "")
        self.error_folder = tk.StringVar(value=self.app.ERROR_FOLDER or "")
        self.log_file_folder = tk.StringVar(value=os.path.dirname(self.app.LOG_FILE) if self.app.LOG_FILE else "")
        
        self.create_widgets()
        
    def create_widgets(self):
        self.frame = ttk.Frame(self.parent, style="Main.TFrame")
        self.frame.pack(fill="both", expand=True)
        
        # Navigation buttons
        self.nav_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.nav_frame.pack(fill="x", pady=(0, 20))
        
        self.home_button = ttk.Button(self.nav_frame, 
                                     text="Sākums", 
                                     command=self.app.show_main_page,
                                     style="TButton",
                                     width=12)
        self.home_button.pack(side="left")
        
        self.settings_button = ttk.Button(self.nav_frame, 
                                        text="Iestatījumi", 
                                        command=self.app.show_config_page,
                                        style="Primary.TButton",
                                        width=12)
        self.settings_button.pack(side="left", padx=(10, 0))
        
        # Main content
        self.content = ttk.Frame(self.frame, padding="20", style="Main.TFrame")
        self.content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ttk.Label(self.content, 
                                    text="Iestatījumi", 
                                    style="Title.TLabel")
        self.title_label.pack(anchor="w", pady=(0, 20))
        
        # Input folder
        self.create_folder_selection_row("XML Failu mape:", self.input_folder)
        
        # Processed folder
        self.create_folder_selection_row("Apstrādāto failu mape:", self.processed_folder)
        
        # Error folder
        self.create_folder_selection_row("Kļūdaino failu mape:", self.error_folder)
        
        # Log file folder
        self.create_folder_selection_row("Žurnāla failu mape:", self.log_file_folder)
        
        # Log file settings frame
        log_settings_frame = ttk.Frame(self.content, style="Main.TFrame")
        log_settings_frame.pack(fill="x", pady=(5, 15))
        
        log_settings_label = ttk.Label(log_settings_frame, 
                                     text="Žurnāla failu iestatījumi:", 
                                     style="TLabel", 
                                     font=("Segoe UI", 11, "bold"))
        log_settings_label.pack(anchor="w", pady=(0, 10))
        
        # Max log file size setting
        self.max_log_size_var = tk.StringVar(value=str(self.app.MAX_LOG_SIZE))
        max_size_frame = ttk.Frame(log_settings_frame, style="Main.TFrame")
        max_size_frame.pack(fill="x", pady=(0, 5))
        
        max_size_label = ttk.Label(max_size_frame, 
                                  text="Maksimālais žurnāla faila izmērs (MB):", 
                                  style="TLabel")
        max_size_label.pack(side="left", padx=(0, 10))
        
        max_size_entry = ttk.Entry(max_size_frame, 
                                 textvariable=self.max_log_size_var, 
                                 width=10)
        max_size_entry.pack(side="left")
        
        # Max record count setting
        self.max_records_var = tk.StringVar(value=str(self.app.MAX_LOG_RECORDS))
        max_records_frame = ttk.Frame(log_settings_frame, style="Main.TFrame")
        max_records_frame.pack(fill="x", pady=(0, 5))
        
        max_records_label = ttk.Label(max_records_frame, 
                                    text="Maksimālais ierakstu skaits žurnāla failā:", 
                                    style="TLabel")
        max_records_label.pack(side="left", padx=(0, 10))
        
        max_records_entry = ttk.Entry(max_records_frame, 
                                    textvariable=self.max_records_var, 
                                    width=10)
        max_records_entry.pack(side="left")
        
        # Log success checkbox
        log_success_frame = ttk.Frame(log_settings_frame, style="Main.TFrame")
        log_success_frame.pack(fill="x", pady=(5, 0))
        
        self.log_success_var = tk.BooleanVar(value=self.app.LOG_SUCCESS)
        log_success_checkbox = ttk.Checkbutton(log_success_frame,
                                             text="Reģistrēt veiksmīgās konversijas žurnālā",
                                             variable=self.log_success_var,
                                             style="TCheckbutton")
        log_success_checkbox.pack(anchor="w")
        
        # Buttons
        self.button_frame = ttk.Frame(self.content, style="Main.TFrame")
        self.button_frame.pack(fill="x", pady=(30, 0))
        
        self.cancel_button = ttk.Button(self.button_frame, 
                                      text="Atcelt", 
                                      command=self.app.show_main_page,
                                      style="TButton",
                                      width=12)
        self.cancel_button.pack(side="right", padx=(10, 0))
        
        self.save_button = ttk.Button(self.button_frame, 
                                     text="Saglabāt", 
                                     command=self.save_config,
                                     style="Primary.TButton",
                                     width=12)
        self.save_button.pack(side="right")
    
    def create_folder_selection_row(self, label_text, string_var):
        frame = ttk.Frame(self.content, style="Main.TFrame")
        frame.pack(fill="x", pady=(0, 15))
        
        label = ttk.Label(frame, text=label_text, style="TLabel")
        label.pack(anchor="w", pady=(0, 5))
        
        selection_frame = ttk.Frame(frame, style="Main.TFrame")
        selection_frame.pack(fill="x")
        
        entry = ttk.Entry(selection_frame, textvariable=string_var, width=50)
        entry.pack(side="left", fill="x", expand=True)
        
        button = ttk.Button(selection_frame, 
                           text="Izvēlēties", 
                           command=lambda sv=string_var: self.browse_folder(sv),
                           style="TButton")
        button.pack(side="right", padx=(10, 0))
    
    def browse_folder(self, string_var):
        folder = filedialog.askdirectory(title="Izvēlieties mapi")
        if folder:
            string_var.set(folder)
    
    def save_config(self):
        # Validate all fields have values
        if not self.input_folder.get():
            messagebox.showwarning("Brīdinājums", "Lūdzu izvēlieties XML failu mapi!")
            return
        
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
        self.app.PROCESSED_FOLDER = self.processed_folder.get() or os.path.join(self.app.INPUT_FOLDER, "Apstrādātie Faili")
        self.app.ERROR_FOLDER = self.error_folder.get() or os.path.join(self.app.INPUT_FOLDER, "Kļūdainie Faili")
        log_folder = self.log_file_folder.get() or self.app.ERROR_FOLDER
        self.app.LOG_FILE = os.path.join(log_folder, "error_log.txt")
        self.app.MAX_LOG_SIZE = max_log_size
        self.app.MAX_LOG_RECORDS = max_records
        self.app.LOG_SUCCESS = self.log_success_var.get()
        
        # Create directories
        os.makedirs(self.app.INPUT_FOLDER, exist_ok=True)
        os.makedirs(self.app.PROCESSED_FOLDER, exist_ok=True)
        os.makedirs(self.app.ERROR_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(self.app.LOG_FILE), exist_ok=True)
        
        # Update main application
        self.app.update_file_list()
        self.app.main_page.config_label.config(text=self.app.INPUT_FOLDER)
        self.app.main_page.status_label.config(text="Iestatījumi veiksmīgi saglabāti", fg=self.app.success_color)
        
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
        
        self.create_widgets()
        
    def create_widgets(self):
        self.frame = ttk.Frame(self.parent, style="Main.TFrame")
        self.frame.pack(fill="both", expand=True)
        
        # Navigation buttons
        self.nav_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.nav_frame.pack(fill="x", pady=(0, 20))
        
        # Make navigation buttons larger
        button_width = 15
        button_pad = 5
        
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
        
        # Title and icon
        self.header_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
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
        self.separator.pack(fill="x", pady=(0, 20))
        
        # Main content
        self.content_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=0)
        
        # Current folder section
        self.folder_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.folder_frame.pack(fill="x", pady=(0, 15))
        
        self.folder_label = ttk.Label(self.folder_frame, 
                                     text="Pašreizējā XML failu mape:", 
                                     style="TLabel")
        self.folder_label.pack(anchor="w", pady=(0, 5))
        
        self.folder_display_frame = ttk.Frame(self.folder_frame, style="Main.TFrame")
        self.folder_display_frame.pack(fill="x")
        
        self.config_label = tk.Label(self.folder_display_frame, 
                                   text="Nav izvēlēta mape", 
                                   font=("Segoe UI", 11),
                                   bg="white", 
                                   fg=self.text_color,
                                   anchor="w",
                                   padx=10,
                                   pady=8,
                                   relief="groove",
                                   bd=1)
        self.config_label.pack(side="left", fill="x", expand=True)
        
        # File selection section
        self.file_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.file_frame.pack(fill="x", pady=(5, 10))
        
        self.file_label = ttk.Label(self.file_frame, 
                                   text="XML Fails:", 
                                   style="TLabel")
        self.file_label.pack(anchor="w", pady=(0, 5))
        
        self.file_dropdown = ttk.Combobox(self.file_frame, 
                                         state="readonly", 
                                         width=50,
                                         height=15)
        self.file_dropdown.pack(fill="x")
        self.file_dropdown.set("Izvēlieties XML failu")
        
        self.description_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.description_frame.pack(fill="x", pady=(5, 20))
        
        self.description_label = tk.Label(self.description_frame, 
                                        text="Izvēlieties XML failu un nospiediet 'Sākt', lai konvertētu uz PDF", 
                                        font=("Segoe UI", 11, "italic"),
                                        bg=self.bg_color, 
                                        fg=self.text_color)
        self.description_label.pack(anchor="w")
        
        # Action button
        self.button_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.button_frame.pack(fill="x", pady=10)
        
        self.start_button = ttk.Button(self.button_frame, 
                                      text="Sākt", 
                                      command=self.app.process_selected_file,
                                      style="Primary.TButton",
                                      width=15)
        self.start_button.pack(side="right")
        
        # Status section
        self.status_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.status_frame.pack(fill="x", pady=(20, 0))
        
        self.file_count_label = tk.Label(self.status_frame,
                                      text="Nav atrasti XML faili",
                                      font=("Segoe UI", 11),
                                      bg=self.bg_color,
                                      fg=self.text_color)
        self.file_count_label.pack(anchor="w", pady=(0, 10))
        
        self.progress_frame = tk.Frame(self.frame, bg=self.secondary_color, height=10)
        self.progress_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        self.status_label = tk.Label(self.frame, 
                                   text="Lūdzu, vispirms konfigurējiet iestatījumus", 
                                   font=("Segoe UI", 11),
                                   bg=self.bg_color, 
                                   fg=self.text_color)
        self.status_label.pack(side="bottom", anchor="w", pady=(10, 0))


class XMLToPDFConverter:
    def __init__(self):
        self.VERSION = APP_VERSION
        self.INPUT_FOLDER = ""
        self.PROCESSED_FOLDER = ""
        self.ERROR_FOLDER = ""
        self.LOG_FILE = ""
        self.MAX_LOG_SIZE = 1  # Default max log file size in MB
        self.MAX_LOG_RECORDS = 100  # Default max number of records in log file
        self.LOG_SUCCESS = False  # Whether to log successful conversions
        self.log_record_count = 0  # Current record count in log file
        
        self.setup_gui()
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("XML uz PDF Konvertētājs")
        
        win_width, win_height = 700, 820  # Increased window size
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
        
        self.main_container = ttk.Frame(self.root, padding="30 20 30 20", style="Main.TFrame")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create pages but only show main page initially
        self.main_page = MainPage(self.main_container, self)
        self.config_page = ConfigPage(self.main_container, self)
        
        # Initially hide config page
        self.config_page.frame.pack_forget()
        
    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        
        style.configure("Main.TFrame", background=self.bg_color)
        
        style.configure("Title.TLabel", 
                        font=("Segoe UI", 20, "bold"), 
                        foreground=self.primary_color, 
                        background=self.bg_color)
        
        style.configure("TLabel", 
                        font=("Segoe UI", 11), 
                        foreground=self.text_color, 
                        background=self.bg_color)
        
        style.configure("Status.TLabel", 
                        font=("Segoe UI", 11), 
                        foreground=self.success_color, 
                        background=self.bg_color)
        
        style.configure("Version.TLabel",
                        font=("Segoe UI", 9),
                        foreground="#777777",
                        background=self.bg_color)
        
        style.configure("TButton", 
                        font=("Segoe UI", 11),
                        background=self.secondary_color,
                        foreground="white")
        
        style.map("TButton",
                  background=[("active", self.primary_color), 
                             ("pressed", "#1b5e20")],
                  relief=[("pressed", "flat"), ("!pressed", "flat")])
        
        style.configure("Primary.TButton", 
                        font=("Segoe UI", 12, "bold"),
                        background=self.secondary_color,
                        foreground="white")
        
        style.map("Primary.TButton",
                  background=[("active", self.primary_color), 
                             ("pressed", "#1b5e20")])
        
        style.configure("TCombobox", 
                        font=("Segoe UI", 11),
                        foreground=self.text_color,
                        fieldbackground="white")
        
        style.configure("TCheckbutton",
                        font=("Segoe UI", 11),
                        foreground=self.text_color,
                        background=self.bg_color)
        
        style.map("TCheckbutton",
                   background=[("active", self.bg_color)])
        
    def create_leaf_icon(self, parent):
        canvas = tk.Canvas(parent, width=30, height=30, bg=self.bg_color, highlightthickness=0)
        
        canvas.create_oval(5, 5, 25, 25, fill=self.secondary_color, outline=self.primary_color)
        canvas.create_arc(8, 8, 22, 22, start=45, extent=180, fill=self.accent_color, outline="")
        canvas.create_line(15, 25, 15, 15, fill=self.primary_color, width=2)
        
        return canvas
    
    def show_main_page(self):
        self.config_page.frame.pack_forget()
        self.main_page.frame.pack(fill="both", expand=True)
    
    def show_config_page(self):
        self.main_page.frame.pack_forget()
        self.config_page.frame.pack(fill="both", expand=True)
        
    def process_selected_file(self):
        if not self.INPUT_FOLDER:
            messagebox.showwarning("Brīdinājums", "Lūdzu vispirms konfigurējiet iestatījumus!")
            self.show_config_page()
            return
            
        selected_file = self.main_page.file_dropdown.get()
        if not selected_file or selected_file == "Izvēlieties XML failu":
            messagebox.showwarning("Brīdinājums", "Lūdzu izvēlieties XML failu!")
            self.main_page.status_label.config(text="Nav izvēlēts fails", fg=self.error_color)
            return
        
        self.main_page.status_label.config(text=f"Apstrādā {selected_file}...", fg=self.text_color)
        self.root.update()
        
        xml_file_path = os.path.join(self.INPUT_FOLDER, selected_file)
        pdf_output_path = os.path.join(self.PROCESSED_FOLDER, selected_file.replace(".xml", ".pdf"))
        
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
                
                shutil.move(xml_file_path, os.path.join(self.PROCESSED_FOLDER, selected_file))
                
                if os.name == "nt":
                    os.startfile(pdf_output_path)
                else:
                    subprocess.run(["xdg-open", pdf_output_path])
                
                self.main_page.status_label.config(text=f"PDF izveidots veiksmīgi: {os.path.basename(pdf_output_path)}", fg=self.success_color)
                messagebox.showinfo("Veiksmīgi", f"PDF izveidots: {pdf_output_path}")
                
                # Log successful conversion if enabled
                self.log_success(selected_file)
            else:
                raise ValueError("cbc:EmbeddedDocumentBinaryObject mezgls netika atrasts")
        except Exception as e:
            error_file_path = os.path.join(self.ERROR_FOLDER, selected_file)
            shutil.move(xml_file_path, error_file_path)
            
            # Log the error in the structured format
            self.log_error(selected_file, str(e))
            
            self.main_page.status_label.config(text=f"Kļūda apstrādājot {selected_file}", fg=self.error_color)
            messagebox.showerror("Kļūda", f"Kļūda apstrādājot failu: {selected_file}\n\nLūdzu pārbaudiet kļūdu žurnālu papildu informācijai.")
        
        self.update_file_list()
        
    def log_error(self, file_name, error_message):
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
    
    def log_success(self, file_name):
        # Only log if LOG_SUCCESS is enabled
        if not self.LOG_SUCCESS:
            return
            
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
    
    def update_file_list(self):
        if not self.INPUT_FOLDER or not os.path.exists(self.INPUT_FOLDER):
            self.main_page.file_dropdown["values"] = ["Izvēlieties XML failu"]
            self.main_page.file_dropdown.current(0)
            self.main_page.file_count_label.config(text="Nav atrasti XML faili")
            return
            
        files = [f for f in os.listdir(self.INPUT_FOLDER) if f.endswith(".xml")]
        
        if files:
            self.main_page.file_dropdown["values"] = files
            self.main_page.file_dropdown.current(0)
            self.main_page.file_count_label.config(text=f"Atrasti {len(files)} XML faili")
            self.main_page.status_label.config(text="Gatavs konvertēšanai", fg=self.success_color)
        else:
            self.main_page.file_dropdown["values"] = ["Izvēlieties XML failu"]
            self.main_page.file_dropdown.current(0)
            self.main_page.file_count_label.config(text="Nav atrasti XML faili")
            self.main_page.status_label.config(text="Izvēlētajā mapē nav atrasti XML faili", fg=self.error_color)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = XMLToPDFConverter()
    app.run()