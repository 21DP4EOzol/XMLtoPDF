import os
import sys
import base64
import logging
import shutil
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import threading
import json
import datetime
from typing import Dict, List, Tuple, Optional
import re
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import queue
import traceback

# Register XML namespaces
NAMESPACES = {
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    # Add more namespaces as needed for different PEPPOL formats
}

class ConfigManager:
    """Manages application configuration settings"""
    DEFAULT_CONFIG = {
        "input_directory": "",
        "output_directory": "",
        "failed_directory": "",
        "log_directory": "",
        "log_max_size_mb": 10,
        "log_max_lines": 10000,
        "log_successful_files": False
    }
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file or return default if file doesn't exist"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error loading config: {str(e)}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except IOError as e:
            logging.error(f"Error saving config: {str(e)}")
            return False
    
    def get(self, key: str, default=None):
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value and save to file"""
        self.config[key] = value
        return self.save_config()


class LogManager:
    """Manages application logging with size and line limits"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.LOG_FILE = None
        self.MAX_LOG_SIZE = self.config.get("log_max_size_mb", 10)  # Default max log file size in MB
        self.MAX_LOG_RECORDS = self.config.get("log_max_lines", 10000)  # Default max number of records in log file
        self.LOG_SUCCESS = self.config.get("log_successful_files", False)  # Whether to log successful conversions
        self.log_record_count = 0  # Current record count in log file
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging based on current settings"""
        log_dir = self.config.get("log_directory")
        if not log_dir:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        
        os.makedirs(log_dir, exist_ok=True)
        
        # Set the log file path
        self.LOG_FILE = os.path.join(log_dir, "error_log.txt")
        
        # Configure the root logger for console output
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler for debugging
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        logging.info(f"Logging initialized. Log file: {self.LOG_FILE}")
    
    def log_error(self, file_name, error_message):
        """Log an error with the standard format"""
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
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                log_dir = os.path.dirname(self.LOG_FILE)
                log_name = os.path.basename(self.LOG_FILE)
                base_name, ext = os.path.splitext(log_name)
                new_log_file = os.path.join(log_dir, f"{base_name}_{timestamp}{ext}")
                self.log_record_count = 0  # Reset count for new file
        
        # Format the error log entry
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"Ielādes datums: {timestamp}\n"
            f"Statuss: KĻŪDA\n"
            f"Faila nosaukums: {file_name}\n"
            f"KĻŪDAS APRAKSTS/PIEZĪMES: {error_message}\n"
            f"{'='*50}\n\n"
        )
        
        # Write to log file
        os.makedirs(os.path.dirname(new_log_file), exist_ok=True)
        with open(new_log_file, "a", encoding="utf-8") as log:
            log.write(log_entry)
        
        # Update record count
        self.log_record_count += 1
        
        # If we created a new file, update the LOG_FILE path
        if new_log_file != self.LOG_FILE:
            self.LOG_FILE = new_log_file
    
    def log_success(self, file_name):
        """Log a successful conversion"""
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
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                log_dir = os.path.dirname(self.LOG_FILE)
                log_name = os.path.basename(self.LOG_FILE)
                base_name, ext = os.path.splitext(log_name)
                new_log_file = os.path.join(log_dir, f"{base_name}_{timestamp}{ext}")
                self.log_record_count = 0
        
        # Format the success log entry
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"Ielādes datums: {timestamp}\n"
            f"Statuss: VEIKSMĪGI\n"
            f"Faila nosaukums: {file_name}\n"
            f"KĻŪDAS APRAKSTS/PIEZĪMES: -\n"
            f"{'='*50}\n\n"
        )
        
        # Write to log file
        os.makedirs(os.path.dirname(new_log_file), exist_ok=True)
        with open(new_log_file, "a", encoding="utf-8") as log:
            log.write(log_entry)
        
        # Update record count
        self.log_record_count += 1
        
        # If we created a new file, update the LOG_FILE path
        if new_log_file != self.LOG_FILE:
            self.LOG_FILE = new_log_file
    
    def update_config(self, log_max_size_mb, log_max_lines, log_successful_files):
        """Update logger configuration"""
        self.MAX_LOG_SIZE = log_max_size_mb
        self.MAX_LOG_RECORDS = log_max_lines
        self.LOG_SUCCESS = log_successful_files


class PeppolConverter:
    """Converts PEPPOL XML files with embedded PDFs to standalone PDF files"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.log_manager = None  # Will be set externally
        self.stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "start_time": datetime.datetime.now()
        }
    
    def set_log_manager(self, log_manager):
        """Set the log manager instance"""
        self.log_manager = log_manager
    
    def process_file(self, xml_file: str) -> Tuple[bool, str]:
        """Process a single XML file to extract embedded PDF
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            filename = os.path.basename(xml_file)
            
            # Standard logging for console
            logging.info(f"Processing {filename}")
            
            # Parse XML
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Register namespaces for XPath
            for prefix, uri in NAMESPACES.items():
                ET.register_namespace(prefix, uri)
            
            # Find embedded document node using XPath-like search
            embedded_doc = None
            for elem in root.iter():
                if elem.tag.endswith('EmbeddedDocumentBinaryObject'):
                    embedded_doc = elem
                    break
            
            if embedded_doc is None:
                error_msg = "No embedded document found in XML"
                # Log the error
                if self.log_manager:
                    self.log_manager.log_error(filename, error_msg)
                return False, error_msg
            
            # Get binary data
            base64_data = embedded_doc.text
            if not base64_data:
                error_msg = "Embedded document contains no data"
                # Log the error
                if self.log_manager:
                    self.log_manager.log_error(filename, error_msg)
                return False, error_msg
            
            # Decode Base64 data
            try:
                binary_data = base64.b64decode(base64_data)
            except Exception as e:
                error_msg = f"Failed to decode Base64 data: {str(e)}"
                # Log the error
                if self.log_manager:
                    self.log_manager.log_error(filename, error_msg)
                return False, error_msg
            
            # Determine output PDF filename and path
            output_dir = self.config.get("output_directory")
            if not output_dir:
                output_dir = os.path.dirname(xml_file)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Create PDF filename from XML filename
            pdf_filename = os.path.splitext(filename)[0] + ".pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            # Write PDF file
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(binary_data)
            
            # Move the original XML file to the output directory
            xml_output_path = os.path.join(output_dir, filename)
            try:
                shutil.move(xml_file, xml_output_path)
                logging.info(f"Moved original XML file to: {xml_output_path}")
            except Exception as move_err:
                logging.warning(f"Failed to move original XML file: {str(move_err)}")
                # Try to copy if move fails
                try:
                    shutil.copy2(xml_file, xml_output_path)
                    logging.info(f"Copied original XML file to: {xml_output_path} (move failed)")
                except Exception as copy_err:
                    logging.error(f"Failed to copy original XML file as fallback: {str(copy_err)}")
            
            # Log success with custom format if enabled
            if self.log_manager:
                self.log_manager.log_success(filename)
            
            return True, pdf_path
            
        except Exception as e:
            error_msg = f"Error processing {os.path.basename(xml_file)}: {str(e)}"
            logging.error(error_msg)
            
            # Log the error
            if self.log_manager:
                self.log_manager.log_error(os.path.basename(xml_file), error_msg)
            
            # Move to failed directory if configured
            failed_dir = self.config.get("failed_directory")
            if failed_dir and failed_dir.strip():
                # Ensure we have an absolute path
                failed_dir = os.path.abspath(failed_dir)
                logging.info(f"Using failed directory: {failed_dir}")
                
                os.makedirs(failed_dir, exist_ok=True)
                try:
                    failed_path = os.path.join(failed_dir, os.path.basename(xml_file))
                    # Move file instead of copying it
                    logging.info(f"Attempting to move failed file from {xml_file} to {failed_path}")
                    shutil.move(xml_file, failed_path)
                    logging.info(f"Moved failed file to: {failed_path}")
                except Exception as move_err:
                    logging.error(f"Failed to move failed file: {str(move_err)}")
                    # Try to copy if move fails
                    try:
                        shutil.copy2(xml_file, os.path.join(failed_dir, os.path.basename(xml_file)))
                        logging.info(f"Copied failed file to: {failed_dir} (move failed)")
                    except Exception as copy_err:
                        logging.error(f"Failed to copy failed file as fallback: {str(copy_err)}")
            else:
                logging.warning(f"Failed directory not configured or empty: '{failed_dir}'")
            
            return False, error_msg
    
    def process_batch(self, files: List[str], progress_callback=None) -> Dict:
        """Process a batch of files with optional progress reporting
        
        Args:
            files: List of file paths to process
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict with processing statistics
        """
        self.stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "start_time": datetime.datetime.now(),
            "failed_files": [],
            "success_files": []
        }
        
        total_files = len(files)
        
        # Process files sequentially
        for i, file in enumerate(files):
            filename = os.path.basename(file)
            
            try:
                success, message = self.process_file(file)
                self.stats["processed"] += 1
                
                if success:
                    self.stats["success"] += 1
                    self.stats.setdefault("success_files", []).append((filename, message))
                else:
                    self.stats["failed"] += 1
                    self.stats.setdefault("failed_files", []).append((filename, message))
                    
            except Exception as e:
                self.stats["processed"] += 1
                self.stats["failed"] += 1
                error_msg = f"Unexpected error: {str(e)}"
                self.stats.setdefault("failed_files", []).append((filename, error_msg))
                
                # Log the error
                if self.log_manager:
                    self.log_manager.log_error(filename, error_msg)
            
            # Update progress
            if progress_callback:
                progress_callback(self.stats["processed"], total_files)
        
        # Calculate elapsed time
        self.stats["end_time"] = datetime.datetime.now()
        self.stats["elapsed_seconds"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        # Standard logging of batch summary
        logging.info(f"Batch processing complete. Processed: {self.stats['processed']}, "
                    f"Success: {self.stats['success']}, Failed: {self.stats['failed']}")
        
        # If only one file was processed successfully, open the PDF
        if len(files) == 1 and self.stats["success"] == 1 and self.stats["success_files"]:
            pdf_path = self.stats["success_files"][0][1]
            if os.path.exists(pdf_path) and pdf_path.lower().endswith('.pdf'):
                self.open_pdf_file(pdf_path)
        
        return self.stats
    
    def open_pdf_file(self, pdf_path):
        """Open the PDF file with the default system viewer"""
        try:
            logging.info(f"Attempting to open PDF: {pdf_path}")
            if sys.platform == 'win32':
                os.startfile(pdf_path)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.Popen(['open', pdf_path])
            else:  # Linux
                import subprocess
                subprocess.Popen(['xdg-open', pdf_path])
            logging.info(f"Successfully opened PDF: {pdf_path}")
        except Exception as e:
            logging.error(f"Failed to open PDF: {str(e)}")


class ConverterGUI:
    """Graphical user interface for the PEPPOL XML to PDF converter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("XML to PDF Converter")
        self.root.geometry("800x600")
        
        # Initialize configuration and logging
        self.config_manager = ConfigManager()
        self.log_manager = LogManager(self.config_manager)
        self.converter = PeppolConverter(self.config_manager)
        self.converter.set_log_manager(self.log_manager)
        
        # Setup drag and drop variables
        self.drag_files = []
        self.currently_processing = False
        self.processing_thread = None
        
        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_converter_tab()
        self.create_config_tab()
        self.create_log_tab()
        
        # Setup drag and drop bindings
        self.setup_drag_drop()
        
        # Periodically check log rotation
        self.check_log_rotation()
    
    def create_converter_tab(self):
        """Create the main converter tab"""
        converter_frame = ttk.Frame(self.notebook)
        self.notebook.add(converter_frame, text="Converter")
        
        # Create drop zone frame
        drop_frame = ttk.LabelFrame(converter_frame, text="Drag and Drop Files Here")
        drop_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Version label (more subtle in the top-right of the drop zone)
        version_label = ttk.Label(drop_frame, text="0.0.3v", font=("Arial", 8))
        version_label.pack(side=tk.TOP, anchor=tk.E, padx=5, pady=2)
        
        # This will be our drop zone
        self.drop_zone = ttk.Label(drop_frame, text="Drop XML files here or select files using the button below")
        self.drop_zone.pack(fill='both', expand=True, padx=20, pady=20)
        
        # File selection button
        select_btn = ttk.Button(drop_frame, text="Select Files", command=self.select_files)
        select_btn.pack(pady=10)
        
        # Process button
        self.process_btn = ttk.Button(drop_frame, text="Process Files", command=self.process_files, state=tk.DISABLED)
        self.process_btn.pack(pady=10)
        
        # Progress frame
        progress_frame = ttk.Frame(converter_frame)
        progress_frame.pack(fill='x', padx=10, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=10, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(padx=10, pady=5)
        
        # Files list
        files_frame = ttk.LabelFrame(converter_frame, text="Selected Files")
        files_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollable file list
        self.files_list = tk.Listbox(files_frame)
        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_list.yview)
        self.files_list.configure(yscrollcommand=scrollbar.set)
        
        self.files_list.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
    
    def create_config_tab(self):
        """Create the configuration tab"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuration")
        
        # Directory selection frame
        dir_frame = ttk.LabelFrame(config_frame, text="Directory Configuration")
        dir_frame.pack(fill='x', padx=10, pady=10)
        
        # Input directory
        ttk.Label(dir_frame, text="Jaunie faili:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.input_dir_var = tk.StringVar(value=self.config_manager.get("input_directory", ""))
        ttk.Entry(dir_frame, textvariable=self.input_dir_var).grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(dir_frame, text="Browse", command=lambda: self.select_directory("input_directory", self.input_dir_var)).grid(row=0, column=2, padx=5, pady=5)
        
        # Output directory
        ttk.Label(dir_frame, text="Apstrādātie faili:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.output_dir_var = tk.StringVar(value=self.config_manager.get("output_directory", ""))
        ttk.Entry(dir_frame, textvariable=self.output_dir_var).grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(dir_frame, text="Browse", command=lambda: self.select_directory("output_directory", self.output_dir_var)).grid(row=1, column=2, padx=5, pady=5)
        
        # Failed directory
        ttk.Label(dir_frame, text="Neapstrādātie faili:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.failed_dir_var = tk.StringVar(value=self.config_manager.get("failed_directory", ""))
        ttk.Entry(dir_frame, textvariable=self.failed_dir_var).grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(dir_frame, text="Browse", command=lambda: self.select_directory("failed_directory", self.failed_dir_var)).grid(row=2, column=2, padx=5, pady=5)
        
        # Log directory
        ttk.Label(dir_frame, text="Ielādes reģistra fails:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.log_dir_var = tk.StringVar(value=self.config_manager.get("log_directory", ""))
        ttk.Entry(dir_frame, textvariable=self.log_dir_var).grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(dir_frame, text="Browse", command=lambda: self.select_directory("log_directory", self.log_dir_var)).grid(row=3, column=2, padx=5, pady=5)
        
        dir_frame.columnconfigure(1, weight=1)
        
        # Log settings frame
        log_frame = ttk.LabelFrame(config_frame, text="Log Settings")
        log_frame.pack(fill='x', padx=10, pady=10)
        
        # Log max size
        ttk.Label(log_frame, text="Max Log Size (MB):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.log_size_var = tk.StringVar(value=str(self.config_manager.get("log_max_size_mb", 10)))
        ttk.Entry(log_frame, textvariable=self.log_size_var, width=10).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Log max lines
        ttk.Label(log_frame, text="Max Log Lines:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.log_lines_var = tk.StringVar(value=str(self.config_manager.get("log_max_lines", 10000)))
        ttk.Entry(log_frame, textvariable=self.log_lines_var, width=10).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Log successful files
        self.log_success_var = tk.BooleanVar(value=self.config_manager.get("log_successful_files", False))
        ttk.Checkbutton(log_frame, text="Record Successful Conversions in Log", variable=self.log_success_var).grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Save button
        save_btn = ttk.Button(config_frame, text="Save Configuration", command=self.save_configuration)
        save_btn.pack(pady=10)
    
    def create_log_tab(self):
        """Create the log viewer tab"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Logs")
        
        # Create log viewer
        self.log_viewer = ScrolledText(log_frame, wrap=tk.WORD)
        self.log_viewer.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Buttons frame
        btn_frame = ttk.Frame(log_frame)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        # Refresh button
        refresh_btn = ttk.Button(btn_frame, text="Refresh Logs", command=self.refresh_logs)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        clear_btn = ttk.Button(btn_frame, text="Clear Viewer", command=self.clear_log_viewer)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Open log directory button
        open_log_dir_btn = ttk.Button(btn_frame, text="Open Log Directory", command=self.open_log_directory)
        open_log_dir_btn.pack(side=tk.LEFT, padx=5)
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        # Check if we're using TkinterDnD
        if hasattr(self.root, 'drop_target_register'):
            # Bind the whole window for drag and drop
            self.root.drop_target_register(self.root.dnd_files)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
            self.drop_zone.configure(text="Drop XML files here or select files using the button below")
        else:
            self.drop_zone.configure(text="Drag and drop not available. Please use 'Select Files' button.")
            logging.warning("TkinterDnD not available, drag and drop will not work")
    
    def handle_drop(self, event):
        """Handle file drop event"""
        if self.currently_processing:
            self.status_var.set("Cannot add files while processing")
            return
        
        # Get the dropped files
        files = event.data
        
        # Parse the file paths (TkDND returns them in a specific format)
        if isinstance(files, str):
            # Handle Windows-style paths with {} and spaces
            if files.startswith('{') and files.endswith('}'):
                files = files[1:-1]
            
            # Split multiple files
            file_list = []
            for item in re.findall(r'{[^}]*}|[^ {}]+', files):
                if item.startswith('{') and item.endswith('}'):
                    file_list.append(item[1:-1])
                else:
                    file_list.append(item)
        else:
            file_list = [files]
        
        # Filter for XML files
        xml_files = [f for f in file_list if f.lower().endswith('.xml')]
        
        if not xml_files:
            self.status_var.set("No XML files were dropped")
            return
        
        # Add to our files list
        for file in xml_files:
            if file not in self.drag_files:
                self.drag_files.append(file)
                self.files_list.insert(tk.END, os.path.basename(file))
        
        # Update status
        self.status_var.set(f"{len(self.drag_files)} files selected")
        
        # Enable process button if we have files
        if self.drag_files:
            self.process_btn.config(state=tk.NORMAL)
    
    def select_files(self):
        """Open file dialog to select XML files"""
        if self.currently_processing:
            return
            
        # Get input directory from config
        initial_dir = self.config_manager.get("input_directory", "")
        if not initial_dir or not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")
        
        # Open file dialog
        files = filedialog.askopenfilenames(
            title="Select XML Files",
            initialdir=initial_dir,
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        
        if not files:
            return
            
        # Add to our files list
        for file in files:
            if file not in self.drag_files:
                self.drag_files.append(file)
                self.files_list.insert(tk.END, os.path.basename(file))
        
        # Update status
        self.status_var.set(f"{len(self.drag_files)} files selected")
        
        # Enable process button if we have files
        if self.drag_files:
            self.process_btn.config(state=tk.NORMAL)
    
    def process_files(self):
        """Process the selected files in a separate thread"""
        if not self.drag_files or self.currently_processing:
            return
        
        # Disable UI elements
        self.currently_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_var.set("Processing files...")
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self.run_processing)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def run_processing(self):
        """Run the file processing in a separate thread"""
        try:
            # Process files with progress callback
            stats = self.converter.process_batch(
                self.drag_files, 
                progress_callback=self.update_progress
            )
            
            # Update UI with results
            self.root.after(0, lambda: self.status_var.set(
                f"Completed: {stats['success']} succeeded, {stats['failed']} failed"
            ))
            
            # Clear file list
            self.root.after(0, self.clear_file_list)
            
            # Refresh logs
            self.root.after(0, self.refresh_logs)
            
        except Exception as e:
            logging.error(f"Processing error: {str(e)}")
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
        
        finally:
            # Re-enable UI
            self.root.after(0, lambda: setattr(self, 'currently_processing', False))
    
    def update_progress(self, current, total):
        """Update progress bar from the processing thread"""
        progress = (current / total) * 100 if total > 0 else 0
        self.root.after(0, lambda: self.progress_var.set(progress))
        self.root.after(0, lambda: self.status_var.set(f"Processing: {current}/{total} files"))
    
    def clear_file_list(self):
        """Clear the file list after processing"""
        self.drag_files = []
        self.files_list.delete(0, tk.END)
        self.process_btn.config(state=tk.DISABLED)
    
    def select_directory(self, config_key, string_var):
        """Open directory selection dialog and update config"""
        initial_dir = string_var.get()
        if not initial_dir or not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")
            
        directory = filedialog.askdirectory(
            title=f"Select {config_key.replace('_', ' ').title()}",
            initialdir=initial_dir
        )
        
        if directory:
            string_var.set(directory)
    
    def save_configuration(self):
        """Save the current configuration settings"""
        try:
            # Update config from UI values
            self.config_manager.set("input_directory", self.input_dir_var.get())
            self.config_manager.set("output_directory", self.output_dir_var.get())
            self.config_manager.set("failed_directory", self.failed_dir_var.get())
            self.config_manager.set("log_directory", self.log_dir_var.get())
            
            # Parse numeric values
            try:
                log_max_size = float(self.log_size_var.get())
                log_max_lines = int(self.log_lines_var.get())
                
                self.config_manager.set("log_max_size_mb", log_max_size)
                self.config_manager.set("log_max_lines", log_max_lines)
                
                # Update the log manager directly
                if hasattr(self, 'log_manager') and self.log_manager:
                    self.log_manager.MAX_LOG_SIZE = log_max_size
                    self.log_manager.MAX_LOG_RECORDS = log_max_lines
                
            except ValueError:
                messagebox.showwarning("Invalid Value", "Numeric values must be integers")
                return
            
            # Save log successful files setting
            log_success = self.log_success_var.get()
            self.config_manager.set("log_successful_files", log_success)
            
            # Update the log manager directly
            if hasattr(self, 'log_manager') and self.log_manager:
                self.log_manager.LOG_SUCCESS = log_success
            
            # Save config
            if self.config_manager.save_config():
                messagebox.showinfo("Success", "Configuration saved successfully")
                
                # Update log manager settings
                if hasattr(self, 'log_manager') and self.log_manager:
                    log_dir = self.log_dir_var.get()
                    if log_dir and not self.log_manager.LOG_FILE:
                        # Create a new log file in the configured directory
                        os.makedirs(log_dir, exist_ok=True)
                        self.log_manager.LOG_FILE = os.path.join(log_dir, "error_log.txt")
            else:
                messagebox.showerror("Error", "Failed to save configuration")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {str(e)}")
    
    def refresh_logs(self):
        """Refresh the log viewer with the latest log content"""
        if not self.log_manager.LOG_FILE or not os.path.exists(self.log_manager.LOG_FILE):
            self.log_viewer.delete(1.0, tk.END)
            self.log_viewer.insert(tk.END, "No log file available")
            return
            
        try:
            # Clear current log view
            self.log_viewer.delete(1.0, tk.END)
            
            # Read and display log file
            with open(self.log_manager.LOG_FILE, 'r', encoding='utf-8') as f:
                log_content = f.read()
                self.log_viewer.insert(tk.END, log_content)
                
            # Auto-scroll to end
            self.log_viewer.see(tk.END)
            
        except Exception as e:
            self.log_viewer.insert(tk.END, f"Error reading log file: {str(e)}")
    
    def clear_log_viewer(self):
        """Clear the log viewer"""
        self.log_viewer.delete(1.0, tk.END)
    
    def open_log_directory(self):
        """Open the log directory in file explorer"""
        log_dir = self.config_manager.get("log_directory")
        if not log_dir or not os.path.isdir(log_dir):
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Open directory in file explorer
        if sys.platform == 'win32':
            os.startfile(log_dir)
        elif sys.platform == 'darwin':  # macOS
            import subprocess
            subprocess.Popen(['open', log_dir])
        else:  # Linux
            import subprocess
            subprocess.Popen(['xdg-open', log_dir])
    
    def check_log_rotation(self):
        """Periodically check if log rotation is needed (not really needed with the new logging system)"""
        # Check again after 5 minutes
        self.root.after(300000, self.check_log_rotation)


def main():
    """Main entry point for the application"""
    try:
        # Try to load TkDND
        try:
            from tkinterdnd2 import TkinterDnD, DND_FILES
            root = TkinterDnD.Tk()
            # For convenience, store the constant
            root.dnd_files = DND_FILES
        except ImportError as e:
            root = tk.Tk()
            logging.warning(f"TkinterDnD2 not available, drag and drop will not work: {str(e)}")
            # Show warning message
            messagebox.showwarning(
                "Missing Dependency", 
                "TkinterDnD2 module not found. Drag and drop functionality will not be available.\n\n"
                "To enable drag and drop, install it with:\npip install tkinterdnd2"
            )
        
        # Create and start application
        app = ConverterGUI(root)
        root.mainloop()
        
    except Exception as e:
        logging.critical(f"Application error: {str(e)}\n{traceback.format_exc()}")
        if 'root' in locals() and isinstance(root, tk.Tk):
            messagebox.showerror("Fatal Error", f"Application encountered a critical error:\n\n{str(e)}")
        else:
            print(f"Fatal error: {str(e)}")


if __name__ == "__main__":
    main()