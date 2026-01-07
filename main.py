import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from resizer import ImageResizer

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Resizer Pro")
        self.geometry("600x500")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # Log area expands

        self.source_dir = ""
        self.dest_dir = ""
        self.resizer = ImageResizer()

        # Source Selection
        self.frame_source = ctk.CTkFrame(self)
        self.frame_source.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.btn_source = ctk.CTkButton(self.frame_source, text="Select Source Folder", command=self.select_source)
        self.btn_source.pack(side="left", padx=10, pady=10)
        self.lbl_source = ctk.CTkLabel(self.frame_source, text="No folder selected", text_color="gray")
        self.lbl_source.pack(side="left", padx=10)

        # Destination Selection
        self.frame_dest = ctk.CTkFrame(self)
        self.frame_dest.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.btn_dest = ctk.CTkButton(self.frame_dest, text="Select Output Folder", command=self.select_dest)
        self.btn_dest.pack(side="left", padx=10, pady=10)
        self.lbl_dest = ctk.CTkLabel(self.frame_dest, text="No folder selected", text_color="gray")
        self.lbl_dest.pack(side="left", padx=10)

        # Options
        self.frame_options = ctk.CTkFrame(self)
        self.frame_options.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.resize_mode = ctk.StringVar(value="percentage")
        
        self.radio_percent = ctk.CTkRadioButton(self.frame_options, text="Percentage %", variable=self.resize_mode, value="percentage", command=self.update_input_label)
        self.radio_percent.grid(row=0, column=0, padx=10, pady=10)
        
        self.radio_width = ctk.CTkRadioButton(self.frame_options, text="Width (px)", variable=self.resize_mode, value="width", command=self.update_input_label)
        self.radio_width.grid(row=0, column=1, padx=10, pady=10)
        
        self.radio_height = ctk.CTkRadioButton(self.frame_options, text="Height (px)", variable=self.resize_mode, value="height", command=self.update_input_label)
        self.radio_height.grid(row=0, column=2, padx=10, pady=10)

        self.radio_max = ctk.CTkRadioButton(self.frame_options, text="Max (px)", variable=self.resize_mode, value="max", command=self.update_input_label)
        self.radio_max.grid(row=0, column=3, padx=10, pady=10)

        self.radio_fit = ctk.CTkRadioButton(self.frame_options, text="Fit (WxH)", variable=self.resize_mode, value="fit", command=self.update_input_label)
        self.radio_fit.grid(row=0, column=4, padx=10, pady=10)

        self.entry_value = ctk.CTkEntry(self.frame_options, placeholder_text="50")
        self.entry_value.grid(row=1, column=0, columnspan=5, padx=10, pady=(0, 10), sticky="ew")

        # Quality
        self.lbl_quality = ctk.CTkLabel(self.frame_options, text="Quality: 95")
        self.lbl_quality.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.slider_quality = ctk.CTkSlider(self.frame_options, from_=1, to=100, number_of_steps=99, command=self.update_quality_label)
        self.slider_quality.set(95)
        self.slider_quality.grid(row=2, column=1, columnspan=4, padx=10, pady=5, sticky="ew")

        # Checkbox for "Do not enlarge"
        self.check_no_enlarge = ctk.CTkCheckBox(self.frame_options, text="Do not enlarge if smaller")
        self.check_no_enlarge.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Checkbox for "Skip Vertical"
        self.check_skip_vertical = ctk.CTkCheckBox(self.frame_options, text="Skip Vertical Images")
        self.check_skip_vertical.grid(row=3, column=2, columnspan=3, padx=10, pady=10, sticky="w")

        # Output Format
        self.lbl_format = ctk.CTkLabel(self.frame_options, text="Output Format:")
        self.lbl_format.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.option_format = ctk.CTkOptionMenu(self.frame_options, values=["JPG", "PNG", "WEBP", "Original"])
        self.option_format.set("JPG")
        self.option_format.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Progress and Action
        self.frame_action = ctk.CTkFrame(self)
        self.frame_action.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_start = ctk.CTkButton(self.frame_action, text="Start Resizing", command=self.start_process, fg_color="green")
        self.btn_start.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.btn_cancel = ctk.CTkButton(self.frame_action, text="Cancel", command=self.cancel_process, fg_color="red", state="disabled")
        self.btn_cancel.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(self.frame_action)
        self.progress_bar.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        self.progress_bar.set(0)

        # Log
        self.textbox_log = ctk.CTkTextbox(self)
        self.textbox_log.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.textbox_log.insert("0.0", "Ready...\n")

    def select_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_dir = path
            self.lbl_source.configure(text=os.path.basename(path) or path)

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_dir = path
            self.lbl_dest.configure(text=os.path.basename(path) or path)

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

    def log(self, message):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")

    def update_progress(self, value):
        self.progress_bar.set(value)

    def start_process(self):
        if not self.source_dir or not self.dest_dir:
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

        self.toggle_ui_state("disabled")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0)
        self.textbox_log.delete("0.0", "end")
        self.log("Starting...")
        
        self.resizer.stop_event.clear()

        params = {
            'mode': self.resize_mode.get(),
            'value': val,
            'quality': int(self.slider_quality.get()),
            'no_enlarge': self.check_no_enlarge.get(),
            'skip_vertical': self.check_skip_vertical.get(),
            'output_format': self.option_format.get()
        }

        thread = threading.Thread(target=self.run_resizer, args=(params,))
        thread.start()

    def cancel_process(self):
        self.resizer.stop()
        self.log("Stopping...")
        self.btn_cancel.configure(state="disabled")

    def run_resizer(self, params):
        try:
            self.resizer.resize_images(
                self.source_dir, 
                self.dest_dir, 
                params, 
                progress_callback=self.update_progress,
                log_callback=self.log
            )
            self.log("Completed Successfully!")
            messagebox.showinfo("Done", "Image resizing completed!")
        except Exception as e:
            self.log(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.toggle_ui_state("normal")
            self.btn_cancel.configure(state="disabled")

    def toggle_ui_state(self, state):
        self.btn_source.configure(state=state)
        self.btn_dest.configure(state=state)
        self.radio_percent.configure(state=state)
        self.radio_width.configure(state=state)
        self.radio_height.configure(state=state)
        self.radio_max.configure(state=state)
        self.radio_fit.configure(state=state)
        self.entry_value.configure(state=state)
        self.slider_quality.configure(state=state)
        self.check_no_enlarge.configure(state=state)
        self.check_skip_vertical.configure(state=state)
        self.option_format.configure(state=state)
        self.btn_start.configure(state=state)

if __name__ == "__main__":
    app = App()
    app.mainloop()
