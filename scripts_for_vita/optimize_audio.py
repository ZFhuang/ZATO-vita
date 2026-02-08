import os
import shutil
import subprocess
import sys
import tempfile

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.join(SCRIPT_DIR, 'ffmpeg.exe')

def download_ffmpeg():
    """Download ffmpeg.exe from official builds"""
    import urllib.request
    import zipfile
    
    # FFmpeg Windows build from gyan.dev (official builds)
    # Using essentials build which is smaller
    download_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    print(f"  - Downloading ffmpeg from official builds...")
    print(f"    URL: {download_url}")
    print(f"    This may take a while (~80MB)...")
    
    try:
        # Download to temp file
        temp_zip = os.path.join(tempfile.gettempdir(), 'ffmpeg.zip')
        
        # Download with progress
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, int(downloaded * 100 / total_size)) if total_size > 0 else 0
            if block_num % 100 == 0:  # Update every 100 blocks
                print(f"    Progress: {percent}%", end='\r')
        
        urllib.request.urlretrieve(download_url, temp_zip, reporthook=download_progress)
        print(f"    Progress: 100%")
        print(f"  - Downloaded to: {temp_zip}")
        
        # Extract
        print(f"  - Extracting (this may take a moment)...")
        extract_dir = os.path.join(tempfile.gettempdir(), 'ffmpeg_extract')
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Find ffmpeg.exe in extracted files (inside bin folder)
        ffmpeg_exe = None
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower() == 'ffmpeg.exe':
                    ffmpeg_exe = os.path.join(root, file)
                    break
            if ffmpeg_exe:
                break
        
        if not ffmpeg_exe:
            print("  ✗ ffmpeg.exe not found in extracted archive")
            return False
        
        # Copy to script directory
        shutil.copy2(ffmpeg_exe, FFMPEG_PATH)
        print(f"  - Copied to: {FFMPEG_PATH}")
        
        # Cleanup
        os.remove(temp_zip)
        shutil.rmtree(extract_dir, ignore_errors=True)
        print(f"  - Cleaned up temporary files")
        
        # Verify
        if os.path.exists(FFMPEG_PATH):
            result = subprocess.run([FFMPEG_PATH, '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0] if result.stdout else "unknown version"
                print(f"  ✓ ffmpeg installed successfully: {version_line}")
                return True
        
        print("  ✗ Installation verification failed")
        return False
        
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        print(f"    Please download manually from: https://ffmpeg.org/download.html")
        print(f"    And place ffmpeg.exe in: {SCRIPT_DIR}")
        return False

# Check if ffmpeg is available
def has_ffmpeg():
    """Check if ffmpeg is available (system PATH or script directory)"""
    if os.path.exists(FFMPEG_PATH):
        return True
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_and_install_ffmpeg():
    """Check ffmpeg and auto-install if missing"""
    if has_ffmpeg():
        return True
    
    print("ffmpeg not found. Attempting auto-installation...")
    print("-" * 60)
    
    # Ask user for confirmation
    if sys.stdin.isatty():  # Interactive mode
        response = input("  Download ffmpeg.exe (~80MB) from official builds? (y/n): ").strip().lower()
        if response not in ('y', 'yes'):
            print("  Auto-installation skipped by user.")
            print("-" * 60)
            return False
    
    success = download_ffmpeg()
    print("-" * 60)
    return success

HAS_FFMPEG = has_ffmpeg()

def get_ffmpeg_cmd():
    """Get ffmpeg command path"""
    if os.path.exists(FFMPEG_PATH):
        return FFMPEG_PATH
    return 'ffmpeg'

# Get project root directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Audio directory
target_dir = os.path.join(base_dir, 'game', 'audio')

# Supported audio formats
supported_formats = ('.mp3', '.ogg', '.wav', '.flac', '.m4a', '.aac')

# Compression config (PS Vita optimization)
AUDIO_CONFIG = {
    # BGM (background music) - larger files, use medium quality
    'bgm': {
        'max_size_mb': 1.0,  # >1MB considered BGM
        'mp3_bitrate': '64k',  # 64kbps, suitable for PS Vita
        'ogg_quality': 3,  # OGG quality 0-10, 3 is good balance
    },
    # SFX (sound effects) - small files, maintain quality
    'sfx': {
        'max_size_mb': 0.1,  # <100KB considered SFX
        'mp3_bitrate': '96k',
        'ogg_quality': 5,
    },
    # Voice - medium quality
    'voice': {
        'folder': 'voice',
        'mp3_bitrate': '80k',
        'ogg_quality': 4,
    }
}

def get_file_size_mb(file_path):
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)

def get_audio_type(file_path, relative_path):
    """Determine audio type"""
    size_mb = get_file_size_mb(file_path)
    
    # Check if in voice folder
    if AUDIO_CONFIG['voice']['folder'] in relative_path.lower():
        return 'voice'
    # >1MB considered BGM
    elif size_mb > AUDIO_CONFIG['bgm']['max_size_mb']:
        return 'bgm'
    # <100KB considered SFX
    elif size_mb < AUDIO_CONFIG['sfx']['max_size_mb']:
        return 'sfx'
    else:
        return 'bgm'  # Default to BGM

def compress_mp3(input_path, output_path, audio_type='bgm'):
    """Compress MP3 using ffmpeg"""
    if not HAS_FFMPEG:
        return False
    
    try:
        bitrate = AUDIO_CONFIG[audio_type]['mp3_bitrate']
        cmd = [
            get_ffmpeg_cmd(),
            '-i', input_path,
            '-codec:a', 'libmp3lame',
            '-b:a', bitrate,
            '-ac', '2',  # Stereo
            '-ar', '44100',  # Sample rate
            '-y',  # Overwrite output file
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"  MP3 compression error: {e}")
        return False

def compress_ogg(input_path, output_path, audio_type='bgm'):
    """Recompress OGG using ffmpeg (or convert to OGG)"""
    if not HAS_FFMPEG:
        return False
    
    try:
        quality = AUDIO_CONFIG[audio_type]['ogg_quality']
        cmd = [
            get_ffmpeg_cmd(),
            '-i', input_path,
            '-codec:a', 'libvorbis',
            '-q:a', str(quality),  # VBR quality
            '-ac', '2',
            '-ar', '44100',
            '-y',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"  OGG compression error: {e}")
        return False

def compress_wav_to_ogg(input_path, output_path, audio_type='bgm'):
    """Compress WAV to OGG"""
    if not HAS_FFMPEG:
        return False
    
    try:
        quality = AUDIO_CONFIG[audio_type]['ogg_quality']
        cmd = [
            get_ffmpeg_cmd(),
            '-i', input_path,
            '-codec:a', 'libvorbis',
            '-q:a', str(quality),
            '-ac', '2',
            '-ar', '44100',
            '-y',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"  WAV conversion error: {e}")
        return False

def optimize_audio(audio_path):
    """Optimize audio file"""
    try:
        rel_path = os.path.relpath(audio_path, base_dir)
        original_size_mb = get_file_size_mb(audio_path)
        file_ext = os.path.splitext(audio_path)[1].lower()
        audio_type = get_audio_type(audio_path, rel_path)
        
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            success = False
            mode = ""
            
            if file_ext == '.mp3':
                success = compress_mp3(audio_path, temp_path, audio_type)
                mode = f"MP3 {AUDIO_CONFIG[audio_type]['mp3_bitrate']}"
            elif file_ext == '.ogg':
                success = compress_ogg(audio_path, temp_path, audio_type)
                mode = f"OGG q{AUDIO_CONFIG[audio_type]['ogg_quality']}"
            elif file_ext == '.wav':
                # WAV to OGG
                ogg_path = temp_path.replace('.wav', '.ogg')
                success = compress_wav_to_ogg(audio_path, ogg_path, audio_type)
                if success:
                    temp_path = ogg_path
                    mode = f"WAV→OGG q{AUDIO_CONFIG[audio_type]['ogg_quality']}"
            else:
                # Other formats to OGG
                ogg_path = temp_path.replace(file_ext, '.ogg')
                success = compress_wav_to_ogg(audio_path, ogg_path, audio_type)
                if success:
                    temp_path = ogg_path
                    mode = f"→OGG q{AUDIO_CONFIG[audio_type]['ogg_quality']}"
            
            if not success:
                os.remove(temp_path)
                return False, f"Compression failed: {rel_path}"
            
            # Check compressed size
            new_size_mb = get_file_size_mb(temp_path)
            saved_mb = original_size_mb - new_size_mb
            
            # If file got larger and not format conversion, keep original
            if saved_mb < -0.01 and file_ext in ('.mp3', '.ogg'):
                os.remove(temp_path)
                return False, f"Skipped (compression increased size): {rel_path} ({original_size_mb:.2f}MB)"
            
            # Determine output path (if format converted, need to change extension)
            if file_ext not in ('.mp3', '.ogg') and success:
                new_path = audio_path.replace(file_ext, '.ogg')
                # Need to update code references, here only handle file
                shutil.move(temp_path, new_path)
                # Delete original file
                os.remove(audio_path)
                return True, f"Converted: {rel_path} → {os.path.basename(new_path)} ({original_size_mb:.2f}MB → {new_size_mb:.2f}MB, saved {saved_mb:.2f}MB) [{mode}]"
            else:
                # Replace original file
                shutil.move(temp_path, audio_path)
                
            if saved_mb > 0.001:
                return True, f"Compressed: {rel_path} ({original_size_mb:.2f}MB → {new_size_mb:.2f}MB, saved {saved_mb:.2f}MB) [{mode}]"
            else:
                return True, f"Processed: {rel_path} ({original_size_mb:.2f}MB) [{mode}]"
                
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
            
    except Exception as e:
        rel_path = os.path.relpath(audio_path, base_dir)
        return False, f"Error processing {rel_path}: {str(e)}"

def process_directory(directory):
    """Recursively process all audio in directory"""
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_saved_mb = 0
    total_increased_mb = 0
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(supported_formats):
                audio_path = os.path.join(root, filename)
                success, message = optimize_audio(audio_path)
                print(message)
                
                if success:
                    processed_count += 1
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
                elif "Error" in message or "failed" in message:
                    error_count += 1
    
    return processed_count, skipped_count, error_count, total_saved_mb, total_increased_mb

def main():
    global HAS_FFMPEG
    
    print("=" * 70)
    print("PS Vita Audio Optimization Tool")
    print("=" * 70)
    
    # Check and auto-install ffmpeg if needed
    if not HAS_FFMPEG:
        if check_and_install_ffmpeg():
            HAS_FFMPEG = True
    
    if HAS_FFMPEG:
        # Show which ffmpeg is being used
        if os.path.exists(FFMPEG_PATH):
            print("✓ ffmpeg enabled (using local: scripts_for_vita/ffmpeg.exe)")
        else:
            print("✓ ffmpeg enabled (using system PATH)")
    else:
        print("! ffmpeg not installed")
        print("  Manual download: https://ffmpeg.org/download.html")
        print("=" * 70)
        return False
    
    print("Compression strategy:")
    print(f"  BGM (>1MB): MP3 64kbps / OGG q3")
    print(f"  SFX (<100KB): MP3 96kbps / OGG q5")
    print(f"  Voice (voice/*): MP3 80kbps / OGG q4")
    print(f"  WAV/Other formats: Convert to OGG")
    print(f"Target directory: game/audio/")
    print("-" * 70)
    
    if os.path.exists(target_dir):
        processed, skipped, errors, saved_mb, increased_mb = process_directory(target_dir)
        
        print("-" * 70)
        if errors > 0:
            print(f"Processing completed with errors!")
        else:
            print(f"Processing complete!")
        print(f"  Optimized: {processed}")
        print(f"  Skipped: {skipped}")
        print(f"  Errors: {errors}")
        if saved_mb > 0:
            print(f"  Total saved: {saved_mb:.2f} MB")
        if increased_mb > 0:
            print(f"  Warning: {increased_mb:.2f} MB files got larger")
        return errors == 0
    else:
        print(f"Error: Audio directory does not exist: {target_dir}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
