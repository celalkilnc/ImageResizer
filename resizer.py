import os
from PIL import Image
import threading

# Disable DecompressionBombError for large images
Image.MAX_IMAGE_PIXELS = None

class ImageResizer:
    def __init__(self):
        self.stop_event = threading.Event()

    def resize_images(self, source_dir, dest_dir, params, progress_callback=None, log_callback=None, skip_callback=None):
        """
        Resizes images from source_dir to dest_dir based on params.
        params: dict with keys 'mode', 'value', 'keep_structure', etc.
        """
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        keep_structure = params.get('keep_structure', True)

        total_files = 0
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
                    total_files += 1

        processed_count = 0
        success_count = 0
        skipped_count = 0
        
        for root, dirs, files in os.walk(source_dir):
            if self.stop_event.is_set():
                break
                
            if keep_structure:
                # Create corresponding structure in dest_dir
                relative_path = os.path.relpath(root, source_dir)
                current_dest_dir = os.path.join(dest_dir, relative_path)
            else:
                # Save everything directly in dest_dir
                current_dest_dir = dest_dir
            
            if not os.path.exists(current_dest_dir):
                os.makedirs(current_dest_dir)

            for file in files:
                if self.stop_event.is_set():
                    break
                    
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
                    source_path = os.path.join(root, file)
                    dest_path = os.path.join(current_dest_dir, file)
                    
                    try:
                        status, message = self._process_image(source_path, dest_path, params)
                        if status == "success":
                            success_count += 1
                            if log_callback:
                                log_callback(f"Processed: {file}")
                        elif status == "skipped":
                            skipped_count += 1
                            if skip_callback:
                                skip_callback(file, message)
                    except Exception as e:
                        skipped_count += 1
                        if skip_callback:
                            skip_callback(file, str(e))
                    
                    processed_count += 1
                    if progress_callback:
                        progress_callback(processed_count / total_files)
        
        return success_count, skipped_count

    def _process_image(self, source_path, dest_path, params):
        with Image.open(source_path) as img:
            original_width, original_height = img.size
            
            if params.get('skip_vertical') and original_height > original_width:
                return "skipped", "vertical"

            if params.get('skip_horizontal') and original_width > original_height:
                return "skipped", "horizontal"

            new_width, new_height = original_width, original_height

            mode = params.get('mode')
            value = params.get('value')

            if mode == 'percentage':
                ratio = value / 100
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
            elif mode == 'width':
                ratio = value / original_width
                new_width = int(value)
                new_height = int(original_height * ratio)
            elif mode == 'height':
                ratio = value / original_height
                new_height = int(value)
                new_width = int(original_width * ratio)
            elif mode == 'max':
                # Resize so that max dimension is 'value', keeping aspect ratio
                ratio = min(value / original_width, value / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
            elif mode == 'fit':
                # Resize to fit within value[0] x value[1], keeping aspect ratio
                max_w, max_h = value
                ratio = min(max_w / original_width, max_h / original_height)
                
                if params.get('no_enlarge') and ratio > 1:
                    ratio = 1
                    
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)

            # High quality resampling
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            quality = params.get('quality', 95)
            output_format = params.get('output_format', 'Original')
            
            save_kwargs = {'quality': quality}
            
            if output_format != 'Original':
                # Change extension
                root, ext = os.path.splitext(dest_path)
                dest_path = root + '.' + output_format.lower()
                
                # Handle format specific requirements
                if output_format == 'JPG':
                    if img_resized.mode in ('RGBA', 'P'):
                        img_resized = img_resized.convert('RGB')
                elif output_format == 'WEBP':
                    save_kwargs['quality'] = quality # WebP also uses quality
                elif output_format == 'PNG':
                    save_kwargs.pop('quality', None) # PNG is lossless, doesn't use quality param in same way (uses compress_level)

            img_resized.save(dest_path, **save_kwargs)
            return "success", None

    def stop(self):
        self.stop_event.set()
