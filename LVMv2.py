import os
import base64
import xml.etree.ElementTree as ET
import shutil
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
from datetime import datetime
import json

APP_VERSION = "0.0.2v"

class XMLToPDFConverter:
    def __init__(self):
        self.VERSION = APP_VERSION
        self.INPUT_FOLDER = ""
        self.PROCESSED_FOLDER = ""
        self.ERROR_FOLDER = ""
        self.LOG_FILE = ""
        self.CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        
        self.load_config() 
        self.setup_gui()
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("XML to PDF Converter")
        
        win_width, win_height = 600, 600
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
        
        self.frame = ttk.Frame(self.root, padding="30 20 30 20", style="Main.TFrame")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.create_widgets()
        
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
        
        style.map("TCombobox",
                  fieldbackground=[("readonly", "white")],
                  selectbackground=[("readonly", self.secondary_color)])
        
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
        
    def create_widgets(self):
        self.header_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.title_frame = ttk.Frame(self.header_frame, style="Main.TFrame")
        self.title_frame.pack(side="left", fill="x")
        
        self.leaf_icon = self.create_leaf_icon(self.title_frame)
        self.leaf_icon.pack(side="left", padx=(0, 10))
        
        self.title_label = ttk.Label(self.title_frame, 
                                    text="XML to PDF Converter", 
                                    style="Title.TLabel")
        self.title_label.pack(side="left")
        
        self.version_label = ttk.Label(self.header_frame,
                                      text=self.VERSION,
                                      style="Version.TLabel")
        self.version_label.pack(side="right", padx=(0, 5))
        
        self.separator = ttk.Separator(self.frame, orient="horizontal")
        self.separator.pack(fill="x", pady=(0, 20))
        
        self.use_config_var = tk.BooleanVar(value=bool(self.INPUT_FOLDER))
        self.use_config_checkbox = ttk.Checkbutton(
            self.frame, 
            text="Izmantot saglabātu konfigurāciju", 
            variable=self.use_config_var,
            command=self.toggle_config_mode,
            style="TCheckbutton"
        )
        self.use_config_checkbox.pack(anchor="w", pady=(0, 10))
        
        self.config_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.config_frame.pack(fill="x", pady=10)
        
        self.folder_label = ttk.Label(self.config_frame, 
                                     text="XML Source Folder:", 
                                     style="TLabel")
        self.folder_label.pack(anchor="w", pady=(0, 5))
        
        self.folder_selection_frame = ttk.Frame(self.config_frame, style="Main.TFrame")
        self.folder_selection_frame.pack(fill="x")
        
        initial_text = self.INPUT_FOLDER if self.INPUT_FOLDER else "Nav izvēlēta mape"
        self.config_label = tk.Label(self.folder_selection_frame, 
                                   text=initial_text, 
                                   font=("Segoe UI", 11),
                                   bg="white", 
                                   fg=self.text_color,
                                   anchor="w",
                                   padx=10,
                                   pady=8,
                                   relief="groove",
                                   bd=1)
        self.config_label.pack(side="left", fill="x", expand=True)
        
        self.config_button = ttk.Button(self.folder_selection_frame, 
                                       text="Izvēlēties mapi", 
                                       command=self.browse_folder,
                                       style="TButton")
        self.config_button.pack(side="right", padx=(10, 0))
        
        self.save_config_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.save_config_frame.pack(fill="x", pady=(5, 15))
        
        self.save_config_button = ttk.Button(self.save_config_frame,
                                           text="Saglabāt konfigurāciju",
                                           command=self.save_config,
                                           style="TButton")
        self.save_config_button.pack(side="right")
        
        self.file_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.file_frame.pack(fill="x", pady=(5, 10))
        
        self.file_label = ttk.Label(self.file_frame, 
                                   text="XML File:", 
                                   style="TLabel")
        self.file_label.pack(anchor="w", pady=(0, 5))
        
        self.file_dropdown = ttk.Combobox(self.file_frame, 
                                         state="readonly", 
                                         width=50,
                                         height=15)
        self.file_dropdown.pack(fill="x")
        self.file_dropdown.set("Select XML file")
        
        self.description_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.description_frame.pack(fill="x", pady=(5, 20))
        
        self.description_label = tk.Label(self.description_frame, 
                                        text="Izvēlieties XML failu un nospiediet 'Start' lai konvertētu uz PDF", 
                                        font=("Segoe UI", 11, "italic"),
                                        bg=self.bg_color, 
                                        fg=self.text_color)
        self.description_label.pack(anchor="w")
        
        self.button_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.button_frame.pack(fill="x", pady=10)
        
        self.start_button = ttk.Button(self.button_frame, 
                                      text="Start", 
                                      command=self.process_selected_file,
                                      style="Primary.TButton",
                                      width=15)
        self.start_button.pack(side="right")
        
        self.status_frame = ttk.Frame(self.frame, style="Main.TFrame")
        self.status_frame.pack(fill="x", pady=(20, 0))
        
        self.file_count_label = tk.Label(self.status_frame,
                                      text="Atrasti 0 XML faili",
                                      font=("Segoe UI", 11),
                                      bg=self.bg_color,
                                      fg=self.text_color)
        self.file_count_label.pack(anchor="w", pady=(0, 10))
        
        self.progress_frame = tk.Frame(self.frame, bg=self.secondary_color, height=10)
        self.progress_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        self.status_label = tk.Label(self.frame, 
                                   text="Ready to convert", 
                                   font=("Segoe UI", 11),
                                   bg=self.bg_color, 
                                   fg=self.success_color)
        self.status_label.pack(side="bottom", anchor="w", pady=(10, 0))
        
        self.toggle_config_mode()
        
        if self.INPUT_FOLDER:
            self.update_file_list()
        
    def load_config(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    folder_path = config.get('input_folder', '')
                    
                    if folder_path and os.path.exists(folder_path):
                        self.configure_folders(folder_path)
                        return True
        except Exception as e:
            print(f"Error loading config: {e}")
        return False
        
    def save_config(self):
        if not self.INPUT_FOLDER:
            messagebox.showwarning("Brīdinājums", "Lūdzu, vispirms izvēlieties mapi!")
            return
            
        try:
            config = {
                'input_folder': self.INPUT_FOLDER,
                'version': self.VERSION
            }
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
                
            self.status_label.config(text="Konfigurācija veiksmīgi saglabāta", fg=self.success_color)
            messagebox.showinfo("Veiksmīgi", "Konfigurācija ir saglabāta")
        except Exception as e:
            self.status_label.config(text=f"Kļūda saglabājot konfigurāciju", fg=self.error_color)
            messagebox.showerror("Kļūda", f"Kļūda saglabājot konfigurāciju: {str(e)}")
            
    def toggle_config_mode(self):
        if self.use_config_var.get():
            self.config_button.config(state="disabled")
            
            config_loaded = self.load_config()
            
            if config_loaded:
                self.status_label.config(text="Izmanto saglabātu konfigurāciju", fg=self.success_color)
            else:
                self.status_label.config(text="Nav atrasta derīga konfigurācija", fg=self.error_color)
                self.use_config_var.set(False)
                self.config_button.config(state="normal")
        else:
            self.config_button.config(state="normal")
            if self.INPUT_FOLDER:
                self.update_file_list()
            
    def configure_folders(self, selected_folder):
        self.INPUT_FOLDER = selected_folder
        self.PROCESSED_FOLDER = os.path.join(selected_folder, "Parstradatie faili")
        self.ERROR_FOLDER = os.path.join(selected_folder, "Kludaini faili")
        self.LOG_FILE = os.path.join(self.ERROR_FOLDER, "error_log.txt")
        
        os.makedirs(self.INPUT_FOLDER, exist_ok=True)
        os.makedirs(self.PROCESSED_FOLDER, exist_ok=True)
        os.makedirs(self.ERROR_FOLDER, exist_ok=True)
        self.update_file_list()
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Izvēlieties XML failu mapi")
        if folder:
            folder_display = folder
            if len(folder) > 50:
                folder_display = folder[:47] + "..."
            self.config_label.config(text=folder_display)
            self.configure_folders(folder)
            self.status_label.config(text=f"Mape veiksmīgi izvēlēta", fg=self.success_color)
        
    def process_selected_file(self):
        selected_file = self.file_dropdown.get()
        if not selected_file or selected_file == "Select XML file":
            messagebox.showwarning("Brīdinājums", "Lūdzu izvēlieties XML failu!")
            self.status_label.config(text="Nav izvēlēts fails", fg=self.error_color)
            return
        
        self.status_label.config(text=f"Apstrādā {selected_file}...", fg=self.text_color)
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
                
                self.status_label.config(text=f"PDF izveidots veiksmīgi: {os.path.basename(pdf_output_path)}", fg=self.success_color)
                messagebox.showinfo("Veiksmīgi", f"PDF izveidots: {pdf_output_path}")
            else:
                raise ValueError("cbc:EmbeddedDocumentBinaryObject mezgls netika atrasts")
        except Exception as e:
            error_file_path = os.path.join(self.ERROR_FOLDER, selected_file)
            shutil.move(xml_file_path, error_file_path)
            
            with open(self.LOG_FILE, "a", encoding="utf-8") as log:
                log_entry = f"{selected_file} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {str(e)}\n"
                log.write(log_entry)
            
            self.status_label.config(text=f"Kļūda apstrādājot {selected_file}", fg=self.error_color)
            messagebox.showerror("Kļūda", f"Kļūda apstrādājot {selected_file}: {str(e)}")
        
        self.update_file_list()
        
    def update_file_list(self):
        if not self.INPUT_FOLDER:
            return
            
        files = [f for f in os.listdir(self.INPUT_FOLDER) if f.endswith(".xml")]
        
        if files:
            self.file_dropdown["values"] = files
            self.file_dropdown.current(0)
            self.file_count_label.config(text=f"Atrasti {len(files)} XML faili")
            self.status_label.config(text="Ready to convert", fg=self.success_color)
        else:
            self.file_dropdown["values"] = ["Select XML file"]
            self.file_dropdown.current(0)
            self.file_count_label.config(text="Nav atrasti XML faili")
            self.status_label.config(text="Nav atrasti XML faili izvēlētajā mapē", fg=self.error_color)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = XMLToPDFConverter()
    app.run()