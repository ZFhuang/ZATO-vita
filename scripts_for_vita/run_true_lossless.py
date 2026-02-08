#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
True lossless processing workflow script (no image/gui optimization)
Execute in order:
1. unpack_and_decompile.py - Unpack and decompile
2. remove_op.py - Remove WebM video references
"""

import os
import sys
import subprocess
from pathlib import Path


def run_script(script_name):
    """Run specified Python script"""
    script_dir = Path(__file__).parent
    script_path = script_dir / script_name
    
    print(f"\n{'='*60}")
    print(f"Executing: {script_name}")
    print(f"{'='*60}")
    
    if not script_path.exists():
        print(f"Error: Script not found {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            cwd=script_dir.parent  # Run in project root directory
        )
        print(f"✓ {script_name} execution complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {script_name} execution failed (return code: {e.returncode})")
        return False
    except Exception as e:
        print(f"✗ {script_name} execution error: {e}")
        return False


def main():
    """Main function"""
    print("="*60)
    print("Starting TRUE lossless processing workflow")
    print("(Only unpacking and WebM removal, no image/gui optimization)")
    print("="*60)
    
    scripts = [
        "unpack_and_decompile.py",
        "remove_op.py"
    ]
    
    success_count = 0
    fail_count = 0
    
    for script in scripts:
        if run_script(script):
            success_count += 1
        else:
            fail_count += 1
            print(f"\n✗ {script} execution failed, stopping workflow")
            break
    
    print(f"\n{'='*60}")
    if fail_count == 0:
        print("True lossless workflow complete")
    else:
        print("Workflow stopped due to error")
    print(f"Success: {success_count}/{len(scripts)}")
    print(f"Failed: {fail_count}/{len(scripts)}")
    print(f"{'='*60}")
    
    return fail_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
