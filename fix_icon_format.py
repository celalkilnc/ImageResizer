from PIL import Image
import os

input_path = 'icon.ico' # Actually a PNG
output_path = 'icon_new.ico'

if os.path.exists(input_path):
    try:
        img = Image.open(input_path)
        # Define the sizes we want in the ICO
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Save as ICO with multiple sizes
        img.save(output_path, format='ICO', sizes=icon_sizes)
        print(f"Successfully converted {input_path} to a proper multi-size ICO: {output_path}")
        
        # Replace the old one
        os.remove(input_path)
        os.rename(output_path, input_path)
        print("Replaced old icon.ico with the new proper ICO.")
    except Exception as e:
        print(f"Error during conversion: {e}")
else:
    print(f"File {input_path} not found.")
