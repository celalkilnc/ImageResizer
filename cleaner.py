import os
import imagehash
from PIL import Image
import threading

class ImageCleaner:
    def __init__(self):
        self.stop_event = threading.Event()

    def find_duplicates(self, source_dir, threshold=5, progress_callback=None, log_callback=None):
        """
        Scans source_dir for images and finds similar ones.
        threshold: Hamming distance threshold (0 = exact match, higher = more tolerant).
        Returns a list of lists, where each inner list contains paths of similar images.
        """
        hashes = {}
        duplicates = []
        image_files = []

        # 1. Collect all image files
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
                    image_files.append(os.path.join(root, file))

        total_files = len(image_files)
        if total_files == 0:
            return []

        # 2. Calculate hashes
        for i, file_path in enumerate(image_files):
            if self.stop_event.is_set():
                break
            
            try:
                with Image.open(file_path) as img:
                    # Use phash (Perceptual Hash)
                    h = imagehash.phash(img)
                    hashes[file_path] = h
            except Exception as e:
                if log_callback:
                    log_callback(f"Error hashing {os.path.basename(file_path)}: {e}")
            
            if progress_callback:
                progress_callback((i + 1) / total_files * 0.5) # First 50% is hashing

        # 3. Compare hashes
        # This is O(N^2) which is slow for many images. 
        # For better performance with many images, we could use a BK-tree or similar, 
        # but for a simple desktop app, a linear scan or grouping by hash might be enough.
        # To support 'threshold', we need to compare.
        
        processed = set()
        keys = list(hashes.keys())
        total_comparisons = len(keys)
        
        for i in range(len(keys)):
            if self.stop_event.is_set():
                break
                
            path1 = keys[i]
            if path1 in processed:
                continue
                
            hash1 = hashes[path1]
            current_group = [path1]
            processed.add(path1)
            
            for j in range(i + 1, len(keys)):
                path2 = keys[j]
                if path2 in processed:
                    continue
                    
                hash2 = hashes[path2]
                if hash1 - hash2 <= threshold:
                    current_group.append(path2)
                    processed.add(path2)
            
            if len(current_group) > 1:
                duplicates.append(current_group)
            
            if progress_callback:
                progress_callback(0.5 + ((i + 1) / total_comparisons * 0.5))

        return duplicates

    def stop(self):
        self.stop_event.set()
