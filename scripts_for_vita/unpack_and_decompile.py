#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unpack game resources and decompile Ren'Py scripts
Features:
1. Use rpatool to unpack .rpa files in game/ folder
2. Use unrpyc to decompile .rpyc files
3. Delete residual .rpa files
"""

import os
import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    base_dir = Path(__file__).parent.parent
    
    # Check rpatool - first check local tools folder (rpatool has no .py extension)
    rpatool_available = False
    local_rpatool = base_dir / "tools" / "rpatool" / "rpatool"
    if local_rpatool.exists():
        rpatool_available = True
    
    # Check if the module can be imported
    if not rpatool_available:
        try:
            result = subprocess.run([sys.executable, "-c", "import rpatool"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                rpatool_available = True
        except Exception:
            pass
    
    # Also check if command line tool is available
    if not rpatool_available:
        try:
            result = subprocess.run(["rpatool", "--help"], capture_output=True, timeout=5)
            if result.returncode == 0:
                rpatool_available = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    # Try to find rpatool.py directly in site-packages
    if not rpatool_available:
        try:
            result = subprocess.run([sys.executable, "-c", 
                "import site; print(site.getsitepackages()[0])"], 
                capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                site_pkg = result.stdout.strip()
                for path in [Path(site_pkg), Path(site_pkg).parent / "site-packages"]:
                    rpatool_path = path / "rpatool.py"
                    if rpatool_path.exists():
                        rpatool_available = True
                        break
        except Exception:
            pass
    
    if not rpatool_available:
        missing.append("rpatool")
    
    # Check unrpyc - first check local tools folder
    unrpyc_available = False
    local_unrpyc = base_dir / "tools" / "unrpyc" / "unrpyc.py"
    if local_unrpyc.exists():
        unrpyc_available = True
    
    # Try import detection
    if not unrpyc_available:
        try:
            result = subprocess.run([sys.executable, "-c", "import unrpyc"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                unrpyc_available = True
        except Exception:
            pass
    
    # Backup detection method - check if unrpyc module exists
    if not unrpyc_available:
        try:
            result = subprocess.run([sys.executable, "-m", "unrpyc", "--help"], 
                                  capture_output=True, timeout=5)
            # unrpyc shows help or error without "No module named"
            if b"No module named" not in result.stderr and b"No module named" not in result.stdout:
                unrpyc_available = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    # Try to find unrpyc.py directly in site-packages
    if not unrpyc_available:
        try:
            result = subprocess.run([sys.executable, "-c", 
                "import site; print(site.getsitepackages()[0])"], 
                capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                site_pkg = result.stdout.strip()
                for path in [Path(site_pkg), Path(site_pkg).parent / "site-packages"]:
                    unrpyc_path = path / "unrpyc.py"
                    if unrpyc_path.exists():
                        unrpyc_available = True
                        break
        except Exception:
            pass
    
    if not unrpyc_available:
        missing.append("unrpyc")
    
    return missing, rpatool_available, unrpyc_available


def install_dependency(dep_name, repo_url):
    """Clone and install dependency from GitHub to project tools folder"""
    import shutil
    
    print(f"\n  Installing {dep_name}...")
    
    # Create tools directory in project root
    base_dir = Path(__file__).parent.parent  # Project root
    tools_dir = base_dir / "tools"
    tools_dir.mkdir(exist_ok=True)
    
    # Set clone directory
    clone_dir = tools_dir / dep_name
    
    try:
        # If directory already exists, remove it first
        if clone_dir.exists():
            print(f"  - Removing existing {dep_name} directory...")
            shutil.rmtree(clone_dir, ignore_errors=True)
        
        # Clone repository
        print(f"  - Cloning from {repo_url}...")
        result = subprocess.run(
            ["git", "clone", repo_url, str(clone_dir)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  ✗ Clone failed: {result.stderr}")
            return False
        
        # Install with pip
        print(f"  - Installing with pip...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(clone_dir)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  ✗ Install failed: {result.stderr}")
            return False
        
        print(f"  ✓ {dep_name} installed successfully to {clone_dir}")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout during installation")
        return False
    except Exception as e:
        print(f"  ✗ Install error: {e}")
        return False


def auto_install_deps(missing_deps):
    """Auto install missing dependencies"""
    dep_repos = {
        "rpatool": "https://codeberg.org/shiz/rpatool.git",
        "unrpyc": "https://github.com/CensoredUsername/unrpyc.git"
    }
    
    success = []
    failed = []
    
    for dep in missing_deps:
        if dep in dep_repos:
            if install_dependency(dep, dep_repos[dep]):
                success.append(dep)
            else:
                failed.append(dep)
        else:
            print(f"  ⚠ Unknown dependency: {dep}")
            failed.append(dep)
    
    return success, failed


def find_rpa_files(game_dir):
    """Find all .rpa files"""
    rpa_files = []
    for file in Path(game_dir).rglob("*.rpa"):
        rpa_files.append(file)
    return rpa_files


def find_rpyc_files(game_dir):
    """Find all .rpyc files"""
    rpyc_files = []
    for file in Path(game_dir).rglob("*.rpyc"):
        rpyc_files.append(file)
    return rpyc_files


def find_rpatool_script():
    """Find rpatool script in project tools folder or site-packages"""
    # First check project local tools folder (rpatool has no .py extension)
    base_dir = Path(__file__).parent.parent
    local_rpatool = base_dir / "tools" / "rpatool" / "rpatool"
    if local_rpatool.exists():
        return str(local_rpatool)
    
    # Then check site-packages
    try:
        result = subprocess.run([sys.executable, "-c", 
            "import site; print(site.getsitepackages()[0])"], 
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            site_pkg = result.stdout.strip()
            for path in [Path(site_pkg), Path(site_pkg).parent / "site-packages"]:
                # rpatool may not have .py extension
                rpatool_path = path / "rpatool"
                if rpatool_path.exists():
                    return str(rpatool_path)
                rpatool_path = path / "rpatool.py"
                if rpatool_path.exists():
                    return str(rpatool_path)
    except Exception:
        pass
    return None


def find_unrpyc_script():
    """Find unrpyc.py in project tools folder or site-packages"""
    # First check project local tools folder
    base_dir = Path(__file__).parent.parent
    local_unrpyc = base_dir / "tools" / "unrpyc" / "unrpyc.py"
    if local_unrpyc.exists():
        return str(local_unrpyc)
    
    # Then check site-packages
    try:
        result = subprocess.run([sys.executable, "-c", 
            "import site; print(site.getsitepackages()[0])"], 
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            site_pkg = result.stdout.strip()
            for path in [Path(site_pkg), Path(site_pkg).parent / "site-packages"]:
                unrpyc_path = path / "unrpyc.py"
                if unrpyc_path.exists():
                    return str(unrpyc_path)
    except Exception:
        pass
    return None


def extract_rpa(rpa_file, output_dir, use_module=False):
    """Unpack .rpa file using rpatool"""
    try:
        # Always try local script first
        rpatool_script = find_rpatool_script()
        if rpatool_script:
            cmd = [sys.executable, rpatool_script, "-x", str(rpa_file), "-o", str(output_dir)]
        elif use_module:
            # Fallback to module mode
            cmd = [sys.executable, "-m", "rpatool", "-x", str(rpa_file), "-o", str(output_dir)]
        else:
            # Use command line mode
            cmd = ["rpatool", "-x", str(rpa_file), "-o", str(output_dir)]
        
        print(f"  Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"  ✓ Successfully unpacked: {rpa_file.name}")
            return True
        else:
            print(f"  ✗ Unpack failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Unpack error: {e}")
        return False


def decompile_rpyc(rpyc_file, output_dir=None):
    """Decompile .rpyc file using unrpyc"""
    try:
        # Try to find unrpyc.py directly first
        unrpyc_script = find_unrpyc_script()
        if unrpyc_script:
            cmd = [sys.executable, unrpyc_script, str(rpyc_file)]
        else:
            # Fallback to module mode
            cmd = [sys.executable, "-m", "unrpyc", str(rpyc_file)]
        
        # If output directory specified
        if output_dir:
            cmd.extend(["-o", str(output_dir)])
        
        print(f"  Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"  ✓ Successfully decompiled: {rpyc_file.name}")
            return True
        else:
            if "already exists" in result.stderr.lower() or "already exists" in result.stdout.lower():
                print(f"  ⚠ File already exists, skipping: {rpyc_file.name}")
                return True
            print(f"  ✗ Decompile failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Decompile error: {e}")
        return False


def delete_rpa_files(rpa_files):
    """Delete .rpa files"""
    deleted = []
    for rpa_file in rpa_files:
        try:
            os.remove(rpa_file)
            deleted.append(rpa_file.name)
            print(f"  ✓ Deleted: {rpa_file.name}")
        except Exception as e:
            print(f"  ✗ Delete failed {rpa_file.name}: {e}")
    return deleted


def delete_rpyc_files(rpyc_files):
    """Delete .rpyc files"""
    deleted = []
    for rpyc_file in rpyc_files:
        try:
            os.remove(rpyc_file)
            deleted.append(rpyc_file.name)
            print(f"  ✓ Deleted: {rpyc_file.name}")
        except Exception as e:
            print(f"  ✗ Delete failed {rpyc_file.name}: {e}")
    return deleted


def main():
    # Check dependencies
    print("=" * 60)
    print("Ren'Py Game Resource Unpack and Decompile Tool")
    print("=" * 60)
    print("\nChecking dependencies...")
    
    missing_deps, rpatool_available, unrpyc_available = check_dependencies()
    
    if missing_deps:
        print("\n✗ Missing following dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        # Ask user if they want to auto install
        print("\nWould you like to automatically install them? (y/n): ", end="")
        response = input().strip().lower()
        
        if response in ('y', 'yes'):
            print("\n" + "-" * 40)
            print("Auto-installing dependencies...")
            print("-" * 40)
            
            success, failed = auto_install_deps(missing_deps)
            
            print("\n" + "-" * 40)
            print("Installation Summary:")
            print("-" * 40)
            
            if success:
                print(f"  ✓ Successfully installed: {', '.join(success)}")
            if failed:
                print(f"  ✗ Failed to install: {', '.join(failed)}")
                print("\n  Please install manually:")
                print("    # rpatool")
                print("    git clone https://codeberg.org/shiz/rpatool.git")
                print("    cd rpatool && pip install -e .")
                print("    # unrpyc")
                print("    git clone https://github.com/CensoredUsername/unrpyc.git")
                print("    cd unrpyc && pip install -e .")
                return False
            
            # Re-check dependencies after installation
            print("\n  Verifying installation...")
            missing_deps, rpatool_available, unrpyc_available = check_dependencies()
            
            if missing_deps:
                print(f"  ✗ Still missing: {', '.join(missing_deps)}")
                return False
            else:
                print("  ✓ All dependencies are now installed!")
        else:
            print("\n  Manual installation instructions:")
            print("    # rpatool")
            print("    git clone https://codeberg.org/shiz/rpatool.git")
            print("    cd rpatool && pip install -e .")
            print("    # unrpyc")
            print("    git clone https://github.com/CensoredUsername/unrpyc.git")
            print("    cd unrpyc && pip install -e .")
            return False
    
    print("✓ All dependencies installed")
    
    # Set paths
    base_dir = Path(__file__).parent.parent  # Project root
    game_dir = base_dir / "game"
    
    print(f"\nGame directory: {game_dir}")
    print()
    
    if not game_dir.exists():
        print(f"Error: Game directory does not exist: {game_dir}")
        return False
    
    has_error = False
    
    # Step 1: Find and unpack .rpa files
    print("Step 1/4: Find and unpack .rpa files")
    print("-" * 40)
    
    rpa_files = find_rpa_files(game_dir)
    
    if not rpa_files:
        print("  No .rpa files found, skipping this step")
    else:
        print(f"  Found {len(rpa_files)} .rpa file(s)")
        
        for rpa_file in rpa_files:
            print(f"\n  Unpacking: {rpa_file.name}")
            if not extract_rpa(rpa_file, game_dir, use_module=not rpatool_available):
                has_error = True
    
    print()
    
    # Step 2: Decompile .rpyc files
    print("Step 2/4: Decompile .rpyc files")
    print("-" * 40)
    
    rpyc_files = find_rpyc_files(game_dir)
    
    if not rpyc_files:
        print("  No .rpyc files found, skipping this step")
    else:
        print(f"  Found {len(rpyc_files)} .rpyc file(s)")
        
        success_count = 0
        for rpyc_file in rpyc_files:
            print(f"\n  Decompiling: {rpyc_file.name}")
            if decompile_rpyc(rpyc_file):
                success_count += 1
            else:
                has_error = True
        
        print(f"\n  Decompile complete: {success_count}/{len(rpyc_files)} successful")
    
    print()
    
    # Step 3: Delete residual .rpa files
    print("Step 3/4: Delete residual .rpa files")
    print("-" * 40)

    # Re-find .rpa files (new ones may have been created during unpacking)
    rpa_files = find_rpa_files(game_dir)

    if not rpa_files:
        print("  No residual .rpa files")
    else:
        print(f"  Found {len(rpa_files)} .rpa file(s)")

        # Directly delete without confirmation
        deleted = delete_rpa_files(rpa_files)
        print(f"\n  Deleted {len(deleted)} file(s)")
    
    print()
    
    # Step 4: Delete decompiled .rpyc files
    print("Step 4/4: Delete decompiled .rpyc files")
    print("-" * 40)

    # Re-find .rpyc files
    rpyc_files = find_rpyc_files(game_dir)

    if not rpyc_files:
        print("  No residual .rpyc files")
    else:
        print(f"  Found {len(rpyc_files)} .rpyc file(s)")

        # Directly delete without confirmation
        deleted = delete_rpyc_files(rpyc_files)
        print(f"\n  Deleted {len(deleted)} file(s)")
    
    print()
    print("=" * 60)
    if has_error:
        print("Processing completed with errors!")
    else:
        print("Processing complete!")
    print("=" * 60)
    return not has_error


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
