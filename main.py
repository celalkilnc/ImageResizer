import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import json
from resizer import ImageResizer
from cleaner import ImageCleaner
from tkinterdnd2 import TkinterDnD, DND_ALL
from locales import TRANSLATIONS
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Configuration File
CONFIG_FILE = "config.json"

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.load_config()
        self.apply_theme()

        self.title(self.t("title"))
        self.geometry("800x800")
        self.minsize(680, 780)
        
        # Set Icon
        try:
            # 1. Register App ID first (Essential for Taskbar)
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("fibula.imageresizer.final.v3")
            except:
                pass

            # 2. Set Icon using standard method
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                # Apply icon both immediately and with a small delay for CTK reliability
                self.iconbitmap(icon_path)
                self.after(300, lambda: self.iconbitmap(icon_path))
        except Exception as e:
            print(f"Icon error: {e}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Tab view expands
        self.grid_rowconfigure(1, weight=0) # Bottom settings button

        # --- Main Tab View ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
        
        self.tab_resizer = self.tab_view.add(self.t("tab_resizer"))
        self.tab_cleaner = self.tab_view.add(self.t("tab_cleaner"))
        
        self.setup_resizer_tab()
        self.setup_cleaner_tab()

        # --- Bottom Settings Button ---
        self.btn_settings = ctk.CTkButton(self, text="⚙", width=30, height=30, command=self.open_settings, font=("Arial", 20), fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"))
        self.btn_settings.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="e")

    def t(self, key):
        return TRANSLATIONS.get(self.config["language"], TRANSLATIONS["en"]).get(key, key)

    def load_config(self):
        default_config = {"language": "en", "theme": "System", "color_theme": "blue"}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config = json.load(f)
            except:
                self.config = default_config
        else:
            self.config = default_config

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    def apply_theme(self):
        ctk.set_appearance_mode(self.config["theme"])
        ctk.set_default_color_theme(self.config["color_theme"])

    def setup_resizer_tab(self):
        self.tab_resizer.grid_columnconfigure(0, weight=1)
        self.tab_resizer.grid_rowconfigure(4, weight=1) # Log area expands (Row 4)

        self.resizer = ImageResizer()
        self.resizer_source_dir = ""
        self.resizer_dest_dir = ""
        self.is_running = False

        # --- Folder Selection ---
        self.frame_folders = ctk.CTkFrame(self.tab_resizer, fg_color="transparent")
        self.frame_folders.grid(row=0, column=0, padx=25, pady=(25, 10), sticky="ew")
        
        # Source
        ctk.CTkLabel(self.frame_folders, text=self.t("source_folder").upper(), font=("Arial", 11, "bold"), text_color="gray60").pack(anchor="w", padx=5)
        self.f_src = ctk.CTkFrame(self.frame_folders, fg_color="transparent")
        self.f_src.pack(fill="x", pady=(2, 12))
        
        self.entry_source = ctk.CTkEntry(self.f_src, placeholder_text=self.t("drag_source"), height=40, border_width=1)
        self.entry_source.pack(side="left", expand=True, fill="x")
        self.entry_source.drop_target_register(DND_ALL)
        self.entry_source.dnd_bind('<<Drop>>', self.drop_source)
        self.entry_source.bind("<KeyRelease>", self.validate_inputs)

        self.btn_source = ctk.CTkButton(self.f_src, text="📂", width=45, height=40, command=self.select_resizer_source, 
                                       fg_color=("gray85", "gray25"), hover_color=("gray75", "gray35"), text_color=("black", "white"))
        self.btn_source.pack(side="left", padx=(8, 0))

        # Destination
        ctk.CTkLabel(self.frame_folders, text=self.t("dest_folder").upper(), font=("Arial", 11, "bold"), text_color="gray60").pack(anchor="w", padx=5)
        self.f_dst = ctk.CTkFrame(self.frame_folders, fg_color="transparent")
        self.f_dst.pack(fill="x", pady=(2, 5))
        
        self.entry_dest = ctk.CTkEntry(self.f_dst, placeholder_text=self.t("drag_dest"), height=40, border_width=1)
        self.entry_dest.pack(side="left", expand=True, fill="x")
        self.entry_dest.drop_target_register(DND_ALL)
        self.entry_dest.dnd_bind('<<Drop>>', self.drop_dest)
        self.entry_dest.bind("<KeyRelease>", self.validate_inputs)

        self.btn_dest = ctk.CTkButton(self.f_dst, text="🎯", width=45, height=40, command=self.select_resizer_dest,
                                     fg_color=("gray85", "gray25"), hover_color=("gray75", "gray35"), text_color=("black", "white"))
        self.btn_dest.pack(side="left", padx=(8, 0))

        # --- Settings & Options Combined Frame ---
        self.frame_config = ctk.CTkFrame(self.tab_resizer)
        self.frame_config.grid(row=1, column=0, padx=15, pady=7, sticky="ew")
        self.frame_config.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(self.frame_config, text=self.t("group_settings"), font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=4, padx=15, pady=(10, 5), sticky="w")
        
        # Resize Mode (Segmented Button)
        self.resize_mode = ctk.StringVar(value="percentage")
        self.modes_dict = {
            self.t("mode_percent"): "percentage",
            self.t("mode_width"): "width",
            self.t("mode_height"): "height",
            self.t("mode_max"): "max",
            self.t("mode_fit"): "fit"
        }
        
        self.seg_button = ctk.CTkSegmentedButton(self.frame_config, 
                                                values=list(self.modes_dict.keys()),
                                                command=self.on_mode_change)
        self.seg_button.set(self.t("mode_percent"))
        self.seg_button.grid(row=1, column=0, columnspan=4, padx=15, pady=10, sticky="ew")

        # Inputs Frame (Dynamic)
        self.frame_inputs = ctk.CTkFrame(self.frame_config, fg_color="transparent")
        self.frame_inputs.grid(row=2, column=0, columnspan=4, padx=15, pady=(0, 10), sticky="ew")
        
        self.entry_value1 = ctk.CTkEntry(self.frame_inputs, placeholder_text="50")
        self.entry_value1.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.entry_value1.bind("<KeyRelease>", self.validate_inputs)
        
        self.entry_value2 = ctk.CTkEntry(self.frame_inputs, placeholder_text="Height")
        self.entry_value2.pack(side="left", expand=True, fill="x", padx=(5, 0))
        self.entry_value2.pack_forget()
        self.entry_value2.bind("<KeyRelease>", self.validate_inputs)

        # Quality & Format Row
        self.lbl_quality = ctk.CTkLabel(self.frame_config, text=f"{self.t('quality')} 95")
        self.lbl_quality.grid(row=3, column=0, padx=(15, 5), pady=5, sticky="w")
        
        self.slider_quality = ctk.CTkSlider(self.frame_config, from_=1, to=100, number_of_steps=99, command=self.update_quality_label)
        self.slider_quality.set(95)
        self.slider_quality.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.frame_config, text=self.t("format")).grid(row=3, column=2, padx=5, pady=5, sticky="e")
        self.option_format = ctk.CTkOptionMenu(self.frame_config, values=["JPG", "PNG", "WEBP", "Original"], width=100)
        self.option_format.set("JPG")
        self.option_format.grid(row=3, column=3, padx=(5, 15), pady=5, sticky="ew")

        # Checkboxes Container
        self.frame_checks = ctk.CTkFrame(self.frame_config, fg_color="transparent")
        self.frame_checks.grid(row=4, column=0, columnspan=4, padx=10, pady=(5, 10), sticky="ew")

        self.check_no_enlarge = ctk.CTkCheckBox(self.frame_checks, text=self.t("no_enlarge"))
        self.check_no_enlarge.pack(side="left", padx=10, pady=5)
        
        self.check_skip_vertical = ctk.CTkCheckBox(self.frame_checks, text=self.t("skip_vertical"))
        self.check_skip_vertical.pack(side="left", padx=10, pady=5)

        self.check_skip_horizontal = ctk.CTkCheckBox(self.frame_checks, text=self.t("skip_horizontal"))
        self.check_skip_horizontal.pack(side="left", padx=10, pady=5)

        self.check_keep_structure = ctk.CTkCheckBox(self.frame_checks, text=self.t("keep_structure"))
        self.check_keep_structure.select()
        self.check_keep_structure.pack(side="left", padx=10, pady=5)

        # --- Action Frame ---
        self.frame_action = ctk.CTkFrame(self.tab_resizer, fg_color="transparent")
        self.frame_action.grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        
        self.btn_toggle = ctk.CTkButton(self.frame_action, text="🚀 " + self.t("start_resizing"), 
                                       command=self.toggle_process, fg_color="gray", state="disabled", 
                                       height=45, font=("Arial", 14, "bold"))
        self.btn_toggle.pack(side="right", padx=0, pady=5, expand=True, fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(self.frame_action, height=12)
        # Initially hidden

        # --- Log Areas ---
        self.frame_logs = ctk.CTkFrame(self.tab_resizer, fg_color="transparent")
        self.frame_logs.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_logs.bind("<Configure>", self.on_logs_frame_configure)
        
        self.log_ratio = 0.5 # Initial ratio
        self.is_horizontal = True # Current layout orientation

        # Success Log
        self.textbox_log = ctk.CTkTextbox(self.frame_logs, state="disabled")
        
        # Splitter Handle
        self.splitter_handle = ctk.CTkFrame(self.frame_logs, width=4, cursor="sb_h_double_arrow", fg_color="gray50")
        self.splitter_handle.bind("<B1-Motion>", self.on_splitter_drag)
        
        # Skipped/Error Log
        self.textbox_skipped = ctk.CTkTextbox(self.frame_logs, state="disabled", text_color="orange")
        
        self.update_logs_layout()

    def update_logs_layout(self):
        width = self.frame_logs.winfo_width()
        if width < 100: # Initial call or too small
            width = 800
            
        if width < 500: # Stack vertically if narrow
            if self.is_horizontal:
                self.is_horizontal = False
                self.textbox_log.grid_forget()
                self.splitter_handle.grid_forget()
                self.textbox_skipped.grid_forget()
                
                self.frame_logs.grid_columnconfigure(0, weight=1)
                self.frame_logs.grid_columnconfigure(1, weight=0)
                self.frame_logs.grid_columnconfigure(2, weight=0)
                self.frame_logs.grid_rowconfigure(0, weight=1)
                self.frame_logs.grid_rowconfigure(2, weight=1)
                
                self.textbox_log.grid(row=0, column=0, pady=(0, 5), sticky="nsew")
                self.textbox_skipped.grid(row=2, column=0, pady=(5, 0), sticky="nsew")
        else: # Horizontal layout with splitter
            if not self.is_horizontal:
                self.is_horizontal = True
                self.textbox_log.grid_forget()
                self.textbox_skipped.grid_forget()
                
                self.frame_logs.grid_rowconfigure(0, weight=1)
                self.frame_logs.grid_rowconfigure(2, weight=0)
            
            # Update Column Weights based on ratio
            r1 = int(self.log_ratio * 100)
            r2 = 100 - r1
            
            self.frame_logs.grid_columnconfigure(0, weight=r1)
            self.frame_logs.grid_columnconfigure(1, weight=0)
            self.frame_logs.grid_columnconfigure(2, weight=r2)
            
            self.textbox_log.grid(row=0, column=0, padx=(0, 2), sticky="nsew")
            self.splitter_handle.grid(row=0, column=1, sticky="ns", padx=2)
            self.textbox_skipped.grid(row=0, column=2, padx=(2, 0), sticky="nsew")

    def on_logs_frame_configure(self, event):
        # Prevent recursion if handled by layout
        if event.widget == self.frame_logs:
            self.update_logs_layout()

    def on_splitter_drag(self, event):
        if not self.is_horizontal: return
        
        # Calculate new ratio based on mouse position relative to frame_logs
        total_width = self.frame_logs.winfo_width()
        if total_width == 0: return
        
        new_ratio = event.x_root - self.frame_logs.winfo_rootx()
        new_ratio = new_ratio / total_width
        
        # Clamping between 0.20 and 0.80
        if new_ratio < 0.20: new_ratio = 0.20
        if new_ratio > 0.80: new_ratio = 0.80
        
        self.log_ratio = new_ratio
        self.update_logs_layout()

    def setup_cleaner_tab(self):
        self.tab_cleaner.grid_columnconfigure(0, weight=1)
        self.tab_cleaner.grid_rowconfigure(2, weight=1)

        self.cleaner = ImageCleaner()
        self.cleaner_source_dir = ""
        self.duplicates = []
        self.check_vars = {}

        # Source Selection
        self.frame_cleaner_source = ctk.CTkFrame(self.tab_cleaner)
        self.frame_cleaner_source.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.frame_cleaner_source.grid_columnconfigure(1, weight=1)

        self.btn_cleaner_source = ctk.CTkButton(self.frame_cleaner_source, text=self.t("select_folder"), command=self.select_cleaner_source)
        self.btn_cleaner_source.grid(row=0, column=0, padx=10, pady=10)
        
        self.entry_cleaner_source = ctk.CTkEntry(self.frame_cleaner_source, placeholder_text=self.t("drag_source"))
        self.entry_cleaner_source.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.entry_cleaner_source.drop_target_register(DND_ALL)
        self.entry_cleaner_source.dnd_bind('<<Drop>>', self.drop_cleaner_source)

        self.btn_scan = ctk.CTkButton(self.frame_cleaner_source, text=self.t("scan"), command=self.start_scan, fg_color="blue")
        self.btn_scan.grid(row=0, column=2, padx=10, pady=10)

        # Action Bar
        self.frame_cleaner_actions = ctk.CTkFrame(self.tab_cleaner)
        self.frame_cleaner_actions.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_select_all = ctk.CTkButton(self.frame_cleaner_actions, text=self.t("select_all"), command=self.select_all_duplicates, width=100)
        self.btn_select_all.pack(side="left", padx=10, pady=5)
        
        self.btn_deselect_all = ctk.CTkButton(self.frame_cleaner_actions, text=self.t("deselect_all"), command=self.deselect_all_duplicates, width=100)
        self.btn_deselect_all.pack(side="left", padx=10, pady=5)

        self.btn_delete_selected = ctk.CTkButton(self.frame_cleaner_actions, text=self.t("delete_selected"), command=self.delete_selected_duplicates, fg_color="red")
        self.btn_delete_selected.pack(side="right", padx=10, pady=5)

        self.cleaner_progress = ctk.CTkProgressBar(self.frame_cleaner_actions)
        self.cleaner_progress.pack(side="bottom", padx=10, pady=5, fill="x")
        self.cleaner_progress.set(0)

        # Results
        self.frame_results = ctk.CTkScrollableFrame(self.tab_cleaner, label_text=self.t("duplicates_found"))
        self.frame_results.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Log
        self.cleaner_log = ctk.CTkTextbox(self.tab_cleaner, height=80)
        self.cleaner_log.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.cleaner_log.insert("0.0", self.t("ready") + "\n")

    # --- Settings Window ---
    def open_settings(self):
        if hasattr(self, 'settings_window') and self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title(self.t("settings"))
        self.settings_window.geometry("400x300")
        self.settings_window.grab_set() # Modal

        # Language
        ctk.CTkLabel(self.settings_window, text=self.t("language")).pack(pady=(20, 5))
        self.option_lang = ctk.CTkOptionMenu(self.settings_window, values=["English", "Türkçe"], command=self.change_language)
        self.option_lang.set("English" if self.config["language"] == "en" else "Türkçe")
        self.option_lang.pack(pady=5)

        # Theme
        ctk.CTkLabel(self.settings_window, text=self.t("theme")).pack(pady=(20, 5))
        self.option_theme = ctk.CTkOptionMenu(self.settings_window, values=["System", "Dark", "Light"], command=self.change_theme)
        self.option_theme.set(self.config["theme"])
        self.option_theme.pack(pady=5)

        # Color Theme
        ctk.CTkLabel(self.settings_window, text=self.t("color_theme")).pack(pady=(20, 5))
        self.option_color = ctk.CTkOptionMenu(self.settings_window, values=["blue", "green", "dark-blue", "red", "violet"], command=self.change_color_theme)
        self.option_color.set(self.config["color_theme"])
        self.option_color.pack(pady=5)

    def change_language(self, choice):
        lang_code = "en" if choice == "English" else "tr"
        if self.config["language"] != lang_code:
            self.config["language"] = lang_code
            self.save_config()
            messagebox.showinfo(self.t("settings"), self.t("restart_required"))

    def change_theme(self, choice):
        self.config["theme"] = choice
        self.save_config()
        ctk.set_appearance_mode(choice)

    def change_color_theme(self, choice):
        if self.config["color_theme"] != choice:
            self.config["color_theme"] = choice
            self.save_config()
            messagebox.showinfo(self.t("settings"), self.t("restart_required"))
            
    def apply_theme(self):
        ctk.set_appearance_mode(self.config["theme"])
        
        color = self.config["color_theme"]
        if color in ["blue", "green", "dark-blue"]:
            ctk.set_default_color_theme(color)
        else:
            # Load custom theme
            try:
                theme_path = resource_path(os.path.join("themes", f"{color}.json"))
                ctk.set_default_color_theme(theme_path)
            except Exception as e:
                print(f"Failed to load theme {color}: {e}")
                ctk.set_default_color_theme("blue")

    # --- Logic Methods ---
    def drop_source(self, event):
        path = event.data.strip('{}')
        self.resizer_source_dir = path
        self.entry_source.delete(0, "end")
        self.entry_source.insert(0, path)
        self.validate_inputs()

    def drop_dest(self, event):
        path = event.data.strip('{}')
        self.resizer_dest_dir = path
        self.entry_dest.delete(0, "end")
        self.entry_dest.insert(0, path)
        self.validate_inputs()

    def drop_cleaner_source(self, event):
        path = event.data.strip('{}')
        self.cleaner_source_dir = path
        self.entry_cleaner_source.delete(0, "end")
        self.entry_cleaner_source.insert(0, path)

    def select_resizer_source(self):
        path = filedialog.askdirectory()
        if path:
            self.resizer_source_dir = path
            self.entry_source.delete(0, "end")
            self.entry_source.insert(0, path)
            self.validate_inputs()

    def select_resizer_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.resizer_dest_dir = path
            self.entry_dest.delete(0, "end")
            self.entry_dest.insert(0, path)
            self.validate_inputs()

    def update_input_fields(self):
        mode = self.resize_mode.get()
        if mode == "fit":
            self.entry_value1.configure(placeholder_text=self.t("mode_width"))
            self.entry_value2.pack(side="left", expand=True, fill="x", padx=(5, 0))
            self.entry_value2.configure(placeholder_text=self.t("mode_height"))
        else:
            self.entry_value2.pack_forget()
            if mode == "percentage":
                self.entry_value1.configure(placeholder_text="e.g. 50")
            else:
                self.entry_value1.configure(placeholder_text="e.g. 1920")
        self.validate_inputs()

    def update_quality_label(self, value):
        self.lbl_quality.configure(text=f"{self.t('quality')} {int(value)}")

    def on_mode_change(self, selected_text):
        mode = self.modes_dict.get(selected_text)
        self.resize_mode.set(mode)
        self.update_input_fields()

    def validate_inputs(self, event=None):
        if self.is_running: return
        source = self.entry_source.get().strip()
        dest = self.entry_dest.get().strip()
        val1 = self.entry_value1.get().strip()
        val2 = self.entry_value2.get().strip()
        mode = self.resize_mode.get()
        is_valid = False
        if source and dest:
            if mode == "fit":
                if val1 and val2: is_valid = True
            else:
                if val1: is_valid = True
        
        if is_valid:
            self.btn_toggle.configure(state="normal", fg_color="green")
        else:
            self.btn_toggle.configure(state="disabled", fg_color="gray")

    def log_resizer(self, message):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def log_skipped(self, filename, reason):
        self.textbox_skipped.configure(state="normal")
        
        # Translate reason if possible
        translated_reason = reason
        if reason == "vertical":
            translated_reason = self.t("skipped_vertical")
        elif reason == "horizontal":
            translated_reason = self.t("skipped_horizontal")
            
        self.textbox_skipped.insert("end", f"{filename}: {translated_reason}\n")
        self.textbox_skipped.see("end")
        self.textbox_skipped.configure(state="disabled")

    def toggle_process(self):
        if self.is_running:
            self.cancel_resizer()
        else:
            self.start_resizer()

    def animate_action_section(self, direction="start"):
        """Animates the button shrinking and progress bar expanding/collapsing with easing."""
        import math
        self.anim_steps = 25 # Increased for smoothness
        self.anim_delay = 10 # ms (approx 100fps)
        
        total_width = self.frame_action.winfo_width()
        if total_width < 100: total_width = 700
        
        target_btn_width = 150
        start_btn_width = total_width
        
        if direction == "start":
            self.progress_bar.pack(side="left", padx=(0, 15), pady=10, expand=True, fill="x")
            self.btn_toggle.pack_configure(expand=False, fill="none")
            self._step_animate(0, start_btn_width, target_btn_width)
        else:
            self._step_animate(0, target_btn_width, start_btn_width, is_reverting=True)

    def _step_animate(self, current_step, start_w, end_w, is_reverting=False):
        import math
        if current_step <= self.anim_steps:
            # Sinusoidal Ease-in-out formula
            t = current_step / self.anim_steps
            easing = -(math.cos(math.pi * t) - 1) / 2
            
            current_w = start_w + (end_w - start_w) * easing
            self.btn_toggle.configure(width=current_w)
            
            self.after(self.anim_delay, lambda: self._step_animate(current_step + 1, start_w, end_w, is_reverting))
        elif is_reverting:
            self.progress_bar.pack_forget()
            self.btn_toggle.pack_configure(expand=True, fill="x")
            self.btn_toggle.configure(width=140)

    def start_resizer(self):
        self.resizer_source_dir = self.entry_source.get()
        self.resizer_dest_dir = self.entry_dest.get()
        if not self.resizer_source_dir or not self.resizer_dest_dir:
            messagebox.showerror("Error", self.t("error_select_dirs"))
            return
        try:
            if self.resize_mode.get() == "fit":
                w = int(self.entry_value1.get())
                h = int(self.entry_value2.get())
                val = (w, h)
            else:
                val = int(self.entry_value1.get())
        except ValueError as e:
            messagebox.showerror("Error", self.t("error_invalid_input").format(e))
            return

        self.is_running = True
        self.btn_toggle.configure(text=self.t("cancel"), fg_color="red")
        self.toggle_resizer_ui("disabled")
        
        self.animate_action_section("start")
        self.progress_bar.set(0)
        
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("0.0", "end")
        self.textbox_log.configure(state="disabled")

        self.textbox_skipped.configure(state="normal")
        self.textbox_skipped.delete("0.0", "end")
        self.textbox_skipped.insert("end", self.t("skipped_log") + "\n\n")
        self.textbox_skipped.configure(state="disabled")
        
        self.log_resizer(self.t("starting"))
        self.resizer.stop_event.clear()

        params = {
            'mode': self.resize_mode.get(),
            'value': val,
            'quality': int(self.slider_quality.get()),
            'no_enlarge': self.check_no_enlarge.get(),
            'skip_vertical': self.check_skip_vertical.get(),
            'skip_horizontal': self.check_skip_horizontal.get(),
            'keep_structure': self.check_keep_structure.get(),
            'output_format': self.option_format.get()
        }
        thread = threading.Thread(target=self.run_resizer_thread, args=(params,))
        thread.start()

    def cancel_resizer(self):
        self.resizer.stop()
        self.log_resizer(self.t("stopping"))

    def run_resizer_thread(self, params):
        try:
            success_count, skipped_count = self.resizer.resize_images(
                self.resizer_source_dir, 
                self.resizer_dest_dir, 
                params, 
                progress_callback=self.progress_bar.set,
                log_callback=self.log_resizer,
                skip_callback=self.log_skipped
            )
            if not self.resizer.stop_event.is_set():
                self.log_resizer("\n" + self.t("completed_count").format(success_count))
                self.log_resizer(self.t("completed"))
                messagebox.showinfo(self.t("done_title"), self.t("completed_count").format(success_count))
            else:
                self.log_resizer(self.t("cancelled"))
        except Exception as e:
            self.log_resizer(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.is_running = False
            self.btn_toggle.configure(text="🚀 " + self.t("start_resizing"), fg_color="green")
            self.animate_action_section("end")
            self.toggle_resizer_ui("normal")
            self.validate_inputs()

    def toggle_resizer_ui(self, state):
        self.btn_source.configure(state=state)
        self.entry_source.configure(state=state)
        self.btn_dest.configure(state=state)
        self.entry_dest.configure(state=state)

    # --- Cleaner Methods ---
    def select_cleaner_source(self):
        path = filedialog.askdirectory()
        if path:
            self.cleaner_source_dir = path
            self.entry_cleaner_source.delete(0, "end")
            self.entry_cleaner_source.insert(0, path)

    def log_cleaner(self, message):
        self.cleaner_log.insert("end", message + "\n")
        self.cleaner_log.see("end")

    def start_scan(self):
        self.cleaner_source_dir = self.entry_cleaner_source.get()
        if not self.cleaner_source_dir:
            messagebox.showerror("Error", self.t("error_select_dirs"))
            return

        self.btn_scan.configure(state="disabled")
        self.cleaner_progress.set(0)
        self.cleaner_log.delete("0.0", "end")
        self.log_cleaner(self.t("starting"))
        
        for widget in self.frame_results.winfo_children():
            widget.destroy()
        self.check_vars.clear()

        self.cleaner.stop_event.clear()
        thread = threading.Thread(target=self.run_scan_thread)
        thread.start()

    def run_scan_thread(self):
        try:
            duplicates = self.cleaner.find_duplicates(
                self.cleaner_source_dir, 
                progress_callback=self.cleaner_progress.set,
                log_callback=self.log_cleaner
            )
            self.duplicates = duplicates
            self.after(0, self.display_duplicates)
            self.log_cleaner(self.t("scan_complete").format(len(duplicates)))
        except Exception as e:
            self.log_cleaner(f"Error: {e}")
        finally:
            self.btn_scan.configure(state="normal")

    def display_duplicates(self):
        if not self.duplicates:
            lbl = ctk.CTkLabel(self.frame_results, text=self.t("no_duplicates"))
            lbl.pack(pady=10)
            return

        for i, group in enumerate(self.duplicates):
            frame_group = ctk.CTkFrame(self.frame_results)
            frame_group.pack(fill="x", padx=5, pady=5)
            
            lbl_group = ctk.CTkLabel(frame_group, text=f"Group {i+1} ({len(group)} files)", font=("Arial", 12, "bold"))
            lbl_group.pack(anchor="w", padx=5, pady=2)

            for file_path in group:
                frame_file = ctk.CTkFrame(frame_group)
                frame_file.pack(fill="x", padx=10, pady=2)
                
                var = ctk.BooleanVar()
                self.check_vars[file_path] = var
                
                chk = ctk.CTkCheckBox(frame_file, text=os.path.basename(file_path), variable=var)
                chk.pack(side="left", padx=5, pady=2)

    def select_all_duplicates(self):
        for var in self.check_vars.values():
            var.set(True)

    def deselect_all_duplicates(self):
        for var in self.check_vars.values():
            var.set(False)

    def delete_selected_duplicates(self):
        selected_files = [path for path, var in self.check_vars.items() if var.get()]
        if not selected_files:
            messagebox.showinfo("Info", "No files selected.")
            return

        if not messagebox.askyesno("Confirm Delete", self.t("confirm_delete").format(len(selected_files))):
            return

        deleted_count = 0
        for path in selected_files:
            try:
                os.remove(path)
                self.log_cleaner(self.t("deleted").format(path))
                deleted_count += 1
            except Exception as e:
                self.log_cleaner(f"Error deleting {path}: {e}")
        
        messagebox.showinfo(self.t("done_title"), self.t("deleted").format(deleted_count))
        self.start_scan()

if __name__ == "__main__":
    app = App()
    app.mainloop()
