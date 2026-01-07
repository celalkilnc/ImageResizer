import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from resizer import ImageResizer
from cleaner import ImageCleaner
from tkinterdnd2 import TkinterDnD, DND_ALL

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Image Resizer & Cleaner Pro")
        self.geometry("800x700")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_resizer = self.tab_view.add("Resizer")
        self.tab_cleaner = self.tab_view.add("Cleaner")
        
        self.setup_resizer_tab()
        self.setup_cleaner_tab()

    def setup_resizer_tab(self):
        self.tab_resizer.grid_columnconfigure(0, weight=1)
        self.tab_resizer.grid_rowconfigure(4, weight=1) # Log area expands

        self.resizer = ImageResizer()
        self.resizer_source_dir = ""
        self.resizer_dest_dir = ""

        # --- Folder Selection Frame ---
        self.frame_folders = ctk.CTkFrame(self.tab_resizer)
        self.frame_folders.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.frame_folders.grid_columnconfigure(1, weight=1)

        # Source
        self.btn_source = ctk.CTkButton(self.frame_folders, text="Source Folder", command=self.select_resizer_source)
        self.btn_source.grid(row=0, column=0, padx=10, pady=10)
        
        self.entry_source = ctk.CTkEntry(self.frame_folders, placeholder_text="Drag & Drop Source Folder Here")
        self.entry_source.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.entry_source.drop_target_register(DND_ALL)
        self.entry_source.dnd_bind('<<Drop>>', self.drop_source)

        # Destination
        self.btn_dest = ctk.CTkButton(self.frame_folders, text="Output Folder", command=self.select_resizer_dest)
        self.btn_dest.grid(row=1, column=0, padx=10, pady=10)
        
        self.entry_dest = ctk.CTkEntry(self.frame_folders, placeholder_text="Drag & Drop Output Folder Here")
        self.entry_dest.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.entry_dest.drop_target_register(DND_ALL)
        self.entry_dest.dnd_bind('<<Drop>>', self.drop_dest)

        # --- Options Frame ---
        self.frame_options = ctk.CTkFrame(self.tab_resizer)
        self.frame_options.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Resize Mode
        self.lbl_mode = ctk.CTkLabel(self.frame_options, text="Resize Mode:", font=("Arial", 12, "bold"))
        self.lbl_mode.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.resize_mode = ctk.StringVar(value="percentage")
        modes = [("Percentage %", "percentage"), ("Width (px)", "width"), ("Height (px)", "height"), ("Max (px)", "max"), ("Fit (WxH)", "fit")]
        
        for i, (text, mode) in enumerate(modes):
            rb = ctk.CTkRadioButton(self.frame_options, text=text, variable=self.resize_mode, value=mode, command=self.update_input_label)
            rb.grid(row=1, column=i, padx=5, pady=5)

        self.entry_value = ctk.CTkEntry(self.frame_options, placeholder_text="50")
        self.entry_value.grid(row=2, column=0, columnspan=5, padx=10, pady=(5, 10), sticky="ew")

        # Settings (Quality, Format, Checks)
        self.frame_settings = ctk.CTkFrame(self.tab_resizer)
        self.frame_settings.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        # Quality
        self.lbl_quality = ctk.CTkLabel(self.frame_settings, text="Quality: 95")
        self.lbl_quality.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.slider_quality = ctk.CTkSlider(self.frame_settings, from_=1, to=100, number_of_steps=99, command=self.update_quality_label)
        self.slider_quality.set(95)
        self.slider_quality.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Format
        self.lbl_format = ctk.CTkLabel(self.frame_settings, text="Format:")
        self.lbl_format.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.option_format = ctk.CTkOptionMenu(self.frame_settings, values=["JPG", "PNG", "WEBP", "Original"])
        self.option_format.set("JPG")
        self.option_format.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

        # Checkboxes
        self.check_no_enlarge = ctk.CTkCheckBox(self.frame_settings, text="Don't Enlarge")
        self.check_no_enlarge.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        self.check_skip_vertical = ctk.CTkCheckBox(self.frame_settings, text="Skip Vertical")
        self.check_skip_vertical.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="w")

        # --- Action Frame ---
        self.frame_action = ctk.CTkFrame(self.tab_resizer)
        self.frame_action.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_start = ctk.CTkButton(self.frame_action, text="Start Resizing", command=self.start_resizer, fg_color="green", height=40)
        self.btn_start.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.btn_cancel = ctk.CTkButton(self.frame_action, text="Cancel", command=self.cancel_resizer, fg_color="red", state="disabled", height=40)
        self.btn_cancel.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(self.frame_action)
        self.progress_bar.pack(side="bottom", padx=10, pady=5, expand=True, fill="x")
        self.progress_bar.set(0)

        # --- Log ---
        self.textbox_log = ctk.CTkTextbox(self.tab_resizer)
        self.textbox_log.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.textbox_log.insert("0.0", "Resizer Ready...\n")

    def setup_cleaner_tab(self):
        self.tab_cleaner.grid_columnconfigure(0, weight=1)
        self.tab_cleaner.grid_rowconfigure(2, weight=1)

        self.cleaner = ImageCleaner()
        self.cleaner_source_dir = ""
        self.duplicates = []
        self.check_vars = {} # Stores checkbox variables

        # Source Selection
        self.frame_cleaner_source = ctk.CTkFrame(self.tab_cleaner)
        self.frame_cleaner_source.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.frame_cleaner_source.grid_columnconfigure(1, weight=1)

        self.btn_cleaner_source = ctk.CTkButton(self.frame_cleaner_source, text="Select Folder", command=self.select_cleaner_source)
        self.btn_cleaner_source.grid(row=0, column=0, padx=10, pady=10)
        
        self.entry_cleaner_source = ctk.CTkEntry(self.frame_cleaner_source, placeholder_text="Drag & Drop Folder Here")
        self.entry_cleaner_source.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.entry_cleaner_source.drop_target_register(DND_ALL)
        self.entry_cleaner_source.dnd_bind('<<Drop>>', self.drop_cleaner_source)

        self.btn_scan = ctk.CTkButton(self.frame_cleaner_source, text="Scan", command=self.start_scan, fg_color="blue")
        self.btn_scan.grid(row=0, column=2, padx=10, pady=10)

        # Action Bar (Select All, Delete Selected)
        self.frame_cleaner_actions = ctk.CTkFrame(self.tab_cleaner)
        self.frame_cleaner_actions.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_select_all = ctk.CTkButton(self.frame_cleaner_actions, text="Select All", command=self.select_all_duplicates, width=100)
        self.btn_select_all.pack(side="left", padx=10, pady=5)
        
        self.btn_deselect_all = ctk.CTkButton(self.frame_cleaner_actions, text="Deselect All", command=self.deselect_all_duplicates, width=100)
        self.btn_deselect_all.pack(side="left", padx=10, pady=5)

        self.btn_delete_selected = ctk.CTkButton(self.frame_cleaner_actions, text="Delete Selected", command=self.delete_selected_duplicates, fg_color="red")
        self.btn_delete_selected.pack(side="right", padx=10, pady=5)

        self.cleaner_progress = ctk.CTkProgressBar(self.frame_cleaner_actions)
        self.cleaner_progress.pack(side="bottom", padx=10, pady=5, fill="x")
        self.cleaner_progress.set(0)

        # Results Area
        self.frame_results = ctk.CTkScrollableFrame(self.tab_cleaner, label_text="Duplicates Found")
        self.frame_results.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Log
        self.cleaner_log = ctk.CTkTextbox(self.tab_cleaner, height=80)
        self.cleaner_log.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.cleaner_log.insert("0.0", "Cleaner Ready...\n")

    # --- Drag & Drop Handlers ---
    def drop_source(self, event):
        path = event.data.strip('{}')
        self.resizer_source_dir = path
        self.entry_source.delete(0, "end")
        self.entry_source.insert(0, path)

    def drop_dest(self, event):
        path = event.data.strip('{}')
        self.resizer_dest_dir = path
        self.entry_dest.delete(0, "end")
        self.entry_dest.insert(0, path)

    def drop_cleaner_source(self, event):
        path = event.data.strip('{}')
        self.cleaner_source_dir = path
        self.entry_cleaner_source.delete(0, "end")
        self.entry_cleaner_source.insert(0, path)

    # --- Resizer Methods ---
    def select_resizer_source(self):
        path = filedialog.askdirectory()
        if path:
            self.resizer_source_dir = path
            self.entry_source.delete(0, "end")
            self.entry_source.insert(0, path)

    def select_resizer_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.resizer_dest_dir = path
            self.entry_dest.delete(0, "end")
            self.entry_dest.insert(0, path)

    def update_input_label(self):
        mode = self.resize_mode.get()
        if mode == "percentage":
            self.entry_value.configure(placeholder_text="e.g. 50 for 50%")
        elif mode == "fit":
            self.entry_value.configure(placeholder_text="e.g. 1024x768")
        else:
            self.entry_value.configure(placeholder_text="e.g. 1920")

    def update_quality_label(self, value):
        self.lbl_quality.configure(text=f"Quality: {int(value)}")

    def log_resizer(self, message):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")

    def start_resizer(self):
        # Update dirs from entries in case user typed/pasted
        self.resizer_source_dir = self.entry_source.get()
        self.resizer_dest_dir = self.entry_dest.get()

        if not self.resizer_source_dir or not self.resizer_dest_dir:
            messagebox.showerror("Error", "Please select both source and destination folders.")
            return

        try:
            if self.resize_mode.get() == "fit":
                val_str = self.entry_value.get().lower().replace('x', ' ').replace(',', ' ')
                parts = val_str.split()
                if len(parts) != 2:
                    raise ValueError("For Fit mode, enter Width x Height (e.g. 1024x768)")
                val = (int(parts[0]), int(parts[1]))
            else:
                val = int(self.entry_value.get())
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            return

        self.toggle_resizer_ui("disabled")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0)
        self.textbox_log.delete("0.0", "end")
        self.log_resizer("Starting...")
        
        self.resizer.stop_event.clear()

        params = {
            'mode': self.resize_mode.get(),
            'value': val,
            'quality': int(self.slider_quality.get()),
            'no_enlarge': self.check_no_enlarge.get(),
            'skip_vertical': self.check_skip_vertical.get(),
            'output_format': self.option_format.get()
        }

        thread = threading.Thread(target=self.run_resizer_thread, args=(params,))
        thread.start()

    def cancel_resizer(self):
        self.resizer.stop()
        self.log_resizer("Stopping...")
        self.btn_cancel.configure(state="disabled")

    def run_resizer_thread(self, params):
        try:
            self.resizer.resize_images(
                self.resizer_source_dir, 
                self.resizer_dest_dir, 
                params, 
                progress_callback=self.progress_bar.set,
                log_callback=self.log_resizer
            )
            self.log_resizer("Completed Successfully!")
            messagebox.showinfo("Done", "Image resizing completed!")
        except Exception as e:
            self.log_resizer(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.toggle_resizer_ui("normal")
            self.btn_cancel.configure(state="disabled")

    def toggle_resizer_ui(self, state):
        self.btn_source.configure(state=state)
        self.entry_source.configure(state=state)
        self.btn_dest.configure(state=state)
        self.entry_dest.configure(state=state)
        # Radio buttons don't have a simple bulk configure, but we can disable the frame or individual
        # For simplicity, just main buttons
        self.btn_start.configure(state=state)

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
            messagebox.showerror("Error", "Please select a folder to scan.")
            return

        self.btn_scan.configure(state="disabled")
        self.cleaner_progress.set(0)
        self.cleaner_log.delete("0.0", "end")
        self.log_cleaner("Scanning for duplicates...")
        
        # Clear previous results
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
            self.log_cleaner(f"Scan complete. Found {len(duplicates)} groups of duplicates.")
        except Exception as e:
            self.log_cleaner(f"Error: {e}")
        finally:
            self.btn_scan.configure(state="normal")

    def display_duplicates(self):
        if not self.duplicates:
            lbl = ctk.CTkLabel(self.frame_results, text="No duplicates found.")
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
                
                # Helper label for full path tooltip-ish
                # lbl_path = ctk.CTkLabel(frame_file, text=file_path, text_color="gray", font=("Arial", 10))
                # lbl_path.pack(side="left", padx=5)

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

        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_files)} files?"):
            return

        deleted_count = 0
        for path in selected_files:
            try:
                os.remove(path)
                self.log_cleaner(f"Deleted: {path}")
                deleted_count += 1
                # Remove widget? Ideally refresh list, but for now just log.
                # To remove widget we'd need to map path to widget.
            except Exception as e:
                self.log_cleaner(f"Error deleting {path}: {e}")
        
        messagebox.showinfo("Done", f"Deleted {deleted_count} files.")
        # Refresh list to remove deleted items visually
        self.start_scan() # Re-scan is safest to update UI correctly

if __name__ == "__main__":
    app = App()
    app.mainloop()
