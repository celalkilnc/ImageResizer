from PIL import Image
import os

icon_path = 'icon.ico'
if os.path.exists(icon_path):
    try:
        img = Image.open(icon_path)
        print(f"Format: {img.format}")
        print(f"Size: {img.size}")
        if hasattr(img, 'info') and 'sizes' in img.info:
            print(f"Sizes in ICO: {img.info['sizes']}")
        else:
            print("No 'sizes' info found in ICO (might only have one size).")
    except Exception as e:
        print(f"Error opening icon: {e}")
else:
    print(f"Icon file {icon_path} not found.")
