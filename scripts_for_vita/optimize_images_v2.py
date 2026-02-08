import os
import shutil
import tempfile
import subprocess
import sys
from PIL import Image

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PNGQUANT_PATH = os.path.join(SCRIPT_DIR, 'pngquant.exe')

def download_pngquant():
    """Download pngquant.exe from official website"""
    import urllib.request
    import zipfile
    
    # pngquant official Windows binary download URL
    download_url = "https://pngquant.org/pngquant-windows.zip"
    
    print(f"  - Downloading pngquant from official website...")
    print(f"    URL: {download_url}")
    
    try:
        # Download to temp file
        temp_zip = os.path.join(tempfile.gettempdir(), 'pngquant.zip')
        
        # Download with progress
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, int(downloaded * 100 / total_size)) if total_size > 0 else 0
            if block_num % 10 == 0:  # Update every 10 blocks
                print(f"    Progress: {percent}%", end='\r')
        
        urllib.request.urlretrieve(download_url, temp_zip, reporthook=download_progress)
        print(f"    Progress: 100%")
        print(f"  - Downloaded to: {temp_zip}")
        
        # Extract
        print(f"  - Extracting...")
        extract_dir = os.path.join(tempfile.gettempdir(), 'pngquant_extract')
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Find pngquant.exe in extracted files
        pngquant_exe = None
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower() == 'pngquant.exe':
                    pngquant_exe = os.path.join(root, file)
                    break
            if pngquant_exe:
                break
        
        if not pngquant_exe:
            print("  ✗ pngquant.exe not found in extracted archive")
            return False
        
        # Copy to script directory
        shutil.copy2(pngquant_exe, PNGQUANT_PATH)
        print(f"  - Copied to: {PNGQUANT_PATH}")
        
        # Cleanup
        os.remove(temp_zip)
        shutil.rmtree(extract_dir, ignore_errors=True)
        
        # Verify
        if os.path.exists(PNGQUANT_PATH):
            result = subprocess.run([PNGQUANT_PATH, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✓ pngquant installed successfully: {result.stdout.strip()}")
                return True
        
        print("  ✗ Installation verification failed")
        return False
        
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        print(f"    Please download manually from: https://github.com/kornelski/pngquant/releases")
        print(f"    And place pngquant.exe in: {SCRIPT_DIR}")
        return False

# Check if pngquant command line tool is available
def has_pngquant():
    """Check if pngquant is available (system PATH or script directory)"""
    # Check script directory first
    if os.path.exists(PNGQUANT_PATH):
        return True
    # Then check system PATH
    try:
        subprocess.run(['pngquant', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_and_install_pngquant():
    """Check pngquant and auto-install if missing"""
    if has_pngquant():
        return True
    
    print("pngquant not found. Attempting auto-installation...")
    print("-" * 60)
    
    # Ask user for confirmation
    if sys.stdin.isatty():  # Interactive mode
        response = input("  Download pngquant.exe from GitHub? (y/n): ").strip().lower()
        if response not in ('y', 'yes'):
            print("  Auto-installation skipped by user.")
            print("-" * 60)
            return False
    
    success = download_pngquant()
    print("-" * 60)
    return success

HAS_PNGQUANT = has_pngquant()

def get_pngquant_cmd():
    """Get pngquant command path"""
    if os.path.exists(PNGQUANT_PATH):
        return PNGQUANT_PATH
    return 'pngquant'

# Get best quantization method
def get_quantize_method(is_rgba=False):
    """Get best quantization method"""
    if is_rgba:
        return Image.Quantize.FASTOCTREE
    else:
        return Image.Quantize.MAXCOVERAGE

def save_png_with_pngquant(img, temp_path, colors=128):
    """Optimize PNG using pngquant command line tool"""
    if not HAS_PNGQUANT:
        return False
    
    try:
        # Save temp PNG first
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_in:
            temp_in = tmp_in.name
        
        # Save as temp file
        if img.mode == 'P':
            img.save(temp_in, 'PNG')
        else:
            # Convert to RGB/RGBA and save
            img.save(temp_in, 'PNG')
        
        # Process with pngquant
        cmd = [
            get_pngquant_cmd(),
            str(colors),
            '--quality=65-80',
            '--speed', '1',  # Highest quality
            '--strip',
            '--force',
            '-o', temp_path,
            temp_in
        ]
        result = subprocess.run(cmd, capture_output=True)
        os.remove(temp_in)
        
        return result.returncode == 0 and os.path.exists(temp_path)
    except Exception:
        return False

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

def get_file_size_mb(file_path):
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)

def has_transparency(img):
    """Check if image has alpha channel"""
    if img.mode in ('RGBA', 'LA', 'PA'):
        # Check if alpha channel has non-fully-opaque pixels
        alpha = img.split()[-1]
        return any(p < 255 for p in alpha.getdata())
    return False

def save_png_optimized(img, temp_path, original_size_mb, force_webp=False):
    """Optimize and save PNG to temp file, return mode used"""
    # Check if has transparency
    transparent = has_transparency(img)
    
    # If force WebP conversion enabled and non-transparent image, convert to WebP
    if force_webp and not transparent:
        if img.mode in ('RGBA', 'LA', 'PA'):
            img = img.convert('RGB')
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        img.save(temp_path, 'WEBP', quality=75, method=6)
        return "WebP(quality 75)"
    
    # If image has transparency, use palette with fewer colors
    if transparent:
        # Transparent images use 64 colors, try pngquant first, otherwise FASTOCTREE
        if HAS_PNGQUANT and save_png_with_pngquant(img, temp_path, 64):
            return "RGBA palette(64 colors+pngquant)"
        method = get_quantize_method(is_rgba=True)
        img_p = img.quantize(colors=64, method=method, dither=Image.Dither.FLOYDSTEINBERG)
        img_p.save(temp_path, 'PNG', optimize=True)
        return "RGBA palette(64 colors+FASTOCTREE+dither)"
    
    # For large files without transparency, use palette mode (lower threshold and colors)
    if original_size_mb > 0.15:
        # Convert to RGB mode
        if img.mode in ('RGBA', 'LA', 'PA'):
            img = img.convert('RGB')
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Try pngquant first, otherwise built-in algorithm
        if HAS_PNGQUANT and save_png_with_pngquant(img, temp_path, 128):
            return "Palette(128 colors+pngquant)"
        method = get_quantize_method(is_rgba=False)
        img_p = img.quantize(colors=128, method=method, dither=Image.Dither.FLOYDSTEINBERG)
        img_p.save(temp_path, 'PNG', optimize=True)
        return "Palette(128 colors+MAXCOVERAGE+dither)"
    # Other files use 32-color palette
    else:
        if img.mode in ('RGBA', 'LA', 'PA'):
            img = img.convert('RGB')
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Try pngquant first, otherwise built-in algorithm
        if HAS_PNGQUANT and save_png_with_pngquant(img, temp_path, 32):
            return "Palette(32 colors+pngquant)"
        method = get_quantize_method(is_rgba=False)
        img_p = img.quantize(colors=32, method=method, dither=Image.Dither.FLOYDSTEINBERG)
        img_p.save(temp_path, 'PNG', optimize=True)
        return "Palette(32 colors+MAXCOVERAGE+dither)"

def optimize_image(image_path):
    """Scale images by uniform ratio for PS Vita screen and compress"""
    try:
        rel_path = os.path.relpath(image_path, base_dir)
        original_size_mb = get_file_size_mb(image_path)
        
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            
            # Calculate new size (scale by 0.75)
            new_width = int(original_width * SCALE_RATIO)
            new_height = int(original_height * SCALE_RATIO)
            
            # If size unchanged, still try to optimize compression
            if new_width == original_width and new_height == original_height:
                # For large files, try re-saving to optimize compression
                if original_size_mb > 0.05:  # Files >50KB try optimization
                    # Use temp file
                    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(image_path)[1], delete=False) as tmp:
                        temp_path = tmp.name
                    
                    try:
                        if img.format == 'PNG':
                            mode = save_png_optimized(img, temp_path, original_size_mb)
                        elif img.format in ('JPEG', 'JPG'):
                            # JPEG reduce quality to 60 (more aggressive)
                            save_img = img.convert('RGB')
                            save_img.save(temp_path, 'JPEG', quality=60, optimize=True, progressive=True)
                            mode = "quality 60"
                        else:
                            img.save(temp_path, img.format, optimize=True)
                            mode = "standard opt"
                        
                        # Check compressed size
                        new_size_mb = get_file_size_mb(temp_path)
                        saved_mb = original_size_mb - new_size_mb
                        
                        if saved_mb > 0.001:  # Accept if saved >1KB
                            # Replace original (use shutil.move for cross-disk support)
                            shutil.move(temp_path, image_path)
                            return True, f"Compressed: {rel_path} ({original_size_mb:.2f}MB -> {new_size_mb:.2f}MB, saved {saved_mb:.2f}MB) [{mode}]"
                        else:
                            # Compression not effective, delete temp, keep original
                            os.remove(temp_path)
                            return False, f"Skipped (poor compression): {rel_path}"
                    except:
                        # Clean up temp file on error
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        raise
                return False, f"Skipped (no change needed): {rel_path}"
            
            # Resize image, use LANCZOS to maintain quality
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(image_path)[1], delete=False) as tmp:
                temp_path = tmp.name
            
            try:
                # Try 1: Save with optimized compression strategy
                if img.format == 'PNG':
                    mode = save_png_optimized(resized_img, temp_path, original_size_mb)
                elif img.format in ('JPEG', 'JPG'):
                    # JPEG reduce quality to 60 to save space (more aggressive)
                    if resized_img.mode in ('RGBA', 'LA', 'P'):
                        resized_img = resized_img.convert('RGB')
                    resized_img.save(temp_path, 'JPEG', quality=60, optimize=True, progressive=True)
                    mode = "quality 60"
                else:
                    # Other formats use original format
                    resized_img.save(temp_path, img.format)
                    mode = "standard"
                
                # Check compressed size
                new_size_mb = get_file_size_mb(temp_path)
                saved_mb = original_size_mb - new_size_mb
                
                # If file got larger, try more conservative save (only resize, no aggressive compression)
                if new_size_mb >= original_size_mb * 0.99:
                    # Try 2: Use basic optimization save
                    if img.format == 'PNG':
                        resized_img.save(temp_path, 'PNG', optimize=True, compress_level=9)
                        mode = "standard compress"
                    elif img.format in ('JPEG', 'JPG'):
                        if resized_img.mode in ('RGBA', 'LA', 'P'):
                            save_img = resized_img.convert('RGB')
                        else:
                            save_img = resized_img
                        save_img.save(temp_path, 'JPEG', quality=70, optimize=True, progressive=True)
                        mode = "quality 70"
                    
                    # Check size again
                    new_size_mb = get_file_size_mb(temp_path)
                    saved_mb = original_size_mb - new_size_mb
                
                # Resize is required, replace regardless of file size
                # Replace original (use shutil.move for cross-disk support)
                shutil.move(temp_path, image_path)
                
                if saved_mb > 0:
                    return True, f"Optimized: {rel_path} ({original_width}x{original_height} -> {new_width}x{new_height}, {original_size_mb:.2f}MB -> {new_size_mb:.2f}MB, saved {saved_mb:.2f}MB) [{mode}]"
                else:
                    return True, f"Resized: {rel_path} ({original_width}x{original_height} -> {new_width}x{new_height}, {original_size_mb:.2f}MB -> {new_size_mb:.2f}MB, increased {abs(saved_mb):.2f}MB) [{mode}]"
            except:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
    
    except Exception as e:
        rel_path = os.path.relpath(image_path, base_dir)
        return False, f"Error processing {rel_path}: {str(e)}"

def process_directory(directory):
    """Recursively process all images in directory"""
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_saved_mb = 0
    total_increased_mb = 0
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(supported_formats):
                image_path = os.path.join(root, filename)
                success, message = optimize_image(image_path)
                print(message)
                
                if success:
                    processed_count += 1
                    # Extract saved or increased size from message
                    if "saved" in message:
                        try:
                            saved_str = message.split("saved ")[1].split("MB")[0]
                            saved_val = float(saved_str)
                            if saved_val > 0:
                                total_saved_mb += saved_val
                            else:
                                total_increased_mb += abs(saved_val)
                        except:
                            pass
                elif "Skipped" in message:
                    skipped_count += 1
                elif "Error" in message:
                    error_count += 1
    
    return processed_count, skipped_count, error_count, total_saved_mb, total_increased_mb

def main():
    global HAS_PNGQUANT
    
    print("=" * 70)
    print("PS Vita Image Optimization Tool")
    print("=" * 70)
    
    # Check and auto-install pngquant if needed
    if not HAS_PNGQUANT:
        if check_and_install_pngquant():
            HAS_PNGQUANT = True
    
    if HAS_PNGQUANT:
        # Show which pngquant is being used
        if os.path.exists(PNGQUANT_PATH):
            print("✓ pngquant enabled (using local: scripts_for_vita/pngquant.exe) - using high quality palette algorithm")
        else:
            print("✓ pngquant enabled (using system PATH) - using high quality palette algorithm")
    else:
        print("! pngquant not installed - using built-in MAXCOVERAGE algorithm")
        print("  Manual download: https://pngquant.org/ (for better color quality)")
    print("Compression strategy: PNG→32-128 color palette, JPEG→quality 60, Transparent PNG→64 color palette")
    print(f"Target directories: game/images/ and game/gui/")
    print(f"Original design resolution: {ORIGINAL_WIDTH}x{ORIGINAL_HEIGHT}")
    print(f"PS Vita resolution: {VITA_WIDTH}x{VITA_HEIGHT}")
    print(f"Uniform scale ratio: {SCALE_RATIO:.4f}")
    print("-" * 70)
    
    total_processed = 0
    total_skipped = 0
    total_errors = 0
    total_saved_mb = 0
    total_increased_mb = 0
    
    for target_dir in target_dirs:
        if os.path.exists(target_dir):
            processed, skipped, errors, saved_mb, increased_mb = process_directory(target_dir)
            total_processed += processed
            total_skipped += skipped
            total_errors += errors
            total_saved_mb += saved_mb
            total_increased_mb += increased_mb
        else:
            print(f"Warning: Directory does not exist, skipping: {target_dir}")
    
    print("-" * 70)
    if total_errors > 0:
        print(f"Processing completed with errors!")
    else:
        print(f"Processing complete!")
    print(f"  Optimized: {total_processed}")
    print(f"  Skipped: {total_skipped}")
    print(f"  Errors: {total_errors}")
    if total_saved_mb > 0:
        print(f"  Total saved: {total_saved_mb:.2f} MB")
    if total_increased_mb > 0:
        print(f"  Warning: {total_increased_mb:.2f} MB files got larger")
    print("=" * 70)
    # Allow up to 10% error rate (tolerate occasional corrupted files)
    total_processed = total_processed + total_skipped + total_errors
    error_rate = total_errors / total_processed if total_processed > 0 else 0
    success = error_rate < 0.10
    if total_errors > 0 and success:
        print(f"Note: {total_errors} errors occurred but error rate ({error_rate:.1%}) is within acceptable threshold")
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
