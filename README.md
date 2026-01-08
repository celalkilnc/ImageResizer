# Image Resizer & Cleaner Pro

A powerful, modern desktop application for batch image resizing and duplicate cleaning. Built with Python and CustomTkinter.


## Features

### 🖼️ Image Resizer
- **Batch Processing**: Resize thousands of images recursively while preserving folder structure.
- **Multiple Modes**:
  - **Percentage**: Scale images by % (e.g., 50%).
  - **Width/Height**: Resize to a fixed width or height.
  - **Max Dimensions**: Fit within a bounding box (maintains aspect ratio).
  - **Fit (WxH)**: Fit exactly within specified Width x Height (maintains aspect ratio).
- **Smart Options**:
  - **Don't Enlarge**: Prevent upscaling smaller images.
  - **Skip Vertical/Horizontal**: Filter images by orientation.
- **Format Conversion**: Convert to JPG, PNG, WEBP, or keep Original format.
- **Quality Control**: Adjust compression quality (1-100).
- **Drag & Drop**: Easily drag folders into the input fields.

### 🧹 Duplicate Cleaner
- **Scan & Detect**: Find duplicate or similar images using Perceptual Hashing (pHash).
- **Grouped Results**: View duplicates side-by-side.
- **Multi-Select**: Select all, deselect all, or manually choose files to delete.
- **Safe Deletion**: Confirmation prompts before deleting files.

## Installation

1. Download the latest `ImageResizerPro.exe` from the [Releases](https://github.com/celalkilnc/ImageResizer/releases) page.
2. Run the executable (No installation required).

## Development

To run the project locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/celalkilnc/ImageResizer.git
   cd ImageResizer
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. Build the executable:
   ```bash
   pyinstaller --noconfirm --onefile --windowed --name "ImageResizerPro" --icon "icon.ico" --add-data "icon.ico;." --collect-all customtkinter --collect-all tkinterdnd2 main.py
   ```

## Technologies Used

- **Python**: Core logic.
- **CustomTkinter**: Modern UI framework.
- **Pillow (PIL)**: Image processing.
- **ImageHash**: Duplicate detection.
- **TkinterDnD2**: Drag and drop support.
- **PyInstaller**: Executable creation.

## License

MIT License. Free to use and modify.
