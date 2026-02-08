import os
from PIL import Image

# Original design resolution
ORIGINAL_WIDTH = 1280
ORIGINAL_HEIGHT = 720
# PS Vita screen resolution
VITA_WIDTH = 960
VITA_HEIGHT = 544

# Uniform scale ratio
SCALE_RATIO = VITA_HEIGHT / ORIGINAL_HEIGHT

# Get parent directory of script directory (project root)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Image directories to process
target_dirs = [
    os.path.join(base_dir, 'game', 'images'),
    os.path.join(base_dir, 'game', 'gui')
]

# Supported image formats
supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

def optimize_image(image_path):
    """Scale images by uniform ratio for PS Vita screen"""
    try:
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            
            # Calculate new size (scale by 0.75)
            new_width = int(original_width * SCALE_RATIO)
            new_height = int(original_height * SCALE_RATIO)
            
            # If size unchanged, skip
            if new_width == original_width and new_height == original_height:
                rel_path = os.path.relpath(image_path, base_dir)
                return False, f"Skipped (no size change): {rel_path}"
            
            # Resize image, use LANCZOS to maintain quality
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save image, keep original format
            if img.format == 'PNG':
                # PNG saved as-is
                resized_img.save(image_path, 'PNG')
            elif img.format in ('JPEG', 'JPG'):
                # JPEG saved with high quality
                resized_img.save(image_path, 'JPEG', quality=95, optimize=True)
            else:
                # Other formats use original format
                resized_img.save(image_path, img.format)
            
            # Show relative path for clarity
            rel_path = os.path.relpath(image_path, base_dir)
            return True, f"Optimized: {rel_path} ({original_width}x{original_height} -> {new_width}x{new_height})"
    
    except Exception as e:
        rel_path = os.path.relpath(image_path, base_dir)
        return False, f"Error processing {rel_path}: {str(e)}"

def process_directory(directory):
    """Recursively process all images in directory"""
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(supported_formats):
                image_path = os.path.join(root, filename)
                success, message = optimize_image(image_path)
                print(message)
                
                if success:
                    processed_count += 1
                elif "Skipped" in message:
                    skipped_count += 1
                elif "Error" in message:
                    error_count += 1
    
    return processed_count, skipped_count, error_count

def main():
    print(f"Starting image optimization...")
    print(f"Target directories: game/images/ and game/gui/")
    print(f"Original design resolution: {ORIGINAL_WIDTH}x{ORIGINAL_HEIGHT}")
    print(f"PS Vita resolution: {VITA_WIDTH}x{VITA_HEIGHT}")
    print(f"Uniform scale ratio: {SCALE_RATIO:.4f}")
    print("-" * 50)
    
    total_processed = 0
    total_skipped = 0
    total_errors = 0
    
    for target_dir in target_dirs:
        if os.path.exists(target_dir):
            processed, skipped, errors = process_directory(target_dir)
            total_processed += processed
            total_skipped += skipped
            total_errors += errors
        else:
            print(f"Warning: Directory does not exist, skipping: {target_dir}")
    
    print("-" * 50)
    print(f"Processing complete!")
    print(f"  Optimized: {total_processed}")
    print(f"  Skipped: {total_skipped}")
    print(f"  Errors: {total_errors}")
    return total_errors == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
