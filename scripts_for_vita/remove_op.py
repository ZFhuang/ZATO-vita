#!/usr/bin/env python3
"""
Adaptive WebM file cleanup script
Features:
1. Automatically scan all .webm files in project and their references in .rpy scripts
2. Automatically comment out movie_cutscene calls
3. Support restore mode (uncomment)
4. Support dry-run mode to preview changes
"""

import os
import re
import sys
import argparse
from pathlib import Path


def get_project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent.resolve()


def find_webm_files(project_root):
    """Recursively find all .webm files"""
    game_dir = project_root / 'game'
    if not game_dir.exists():
        return []
    
    webm_files = []
    for webm_path in game_dir.rglob('*.webm'):
        webm_files.append(webm_path)
    return webm_files


def find_rpy_files(project_root):
    """Recursively find all .rpy script files"""
    game_dir = project_root / 'game'
    if not game_dir.exists():
        return []
    
    rpy_files = []
    for rpy_path in game_dir.rglob('*.rpy'):
        rpy_files.append(rpy_path)
    return rpy_files


def find_webm_references(rpy_file, webm_names):
    """
    Find webm references in .rpy file
    Returns: [(line_num, original_line, is_movie_cutscene), ...]
    """
    references = []
    try:
        with open(rpy_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  Warning: Cannot read file {rpy_file}: {e}")
        return references
    
    # Match movie_cutscene calls or any lines containing webm names
    for line_num, line in enumerate(lines, 1):
        for webm_name in webm_names:
            if webm_name in line:
                is_movie_cutscene = 'movie_cutscene' in line
                references.append((line_num, line, is_movie_cutscene))
                break
    
    return references


def comment_webm_lines(rpy_file, dry_run=False):
    """Comment out lines containing webm (especially movie_cutscene calls)
    Returns: (modified, error) - modified is True if changes were made, error is True if an error occurred
    """
    try:
        with open(rpy_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines(keepends=True)
    except Exception as e:
        print(f"  Error: Cannot read file {rpy_file}: {e}")
        return False, True
    
    modified = False
    new_lines = []
    commented_count = 0
    
    # Regex: match movie_cutscene calls (including indented)
    movie_pattern = re.compile(r'^(\s*)((\$|python:\s*)?\s*renpy\.movie_cutscene\s*\(.*\.webm.*\))', re.IGNORECASE)
    # Regex: match any code line containing .webm (excluding already commented)
    webm_pattern = re.compile(r'^(\s*)([^#\n]*\.webm)', re.IGNORECASE)
    
    for line in lines:
        stripped = line.lstrip()
        
        # Skip already commented lines
        if stripped.startswith('#'):
            new_lines.append(line)
            continue
        
        # Try to match movie_cutscene
        match = movie_pattern.match(line)
        if match:
            indent = match.group(1)
            code = match.group(2)
            new_line = f"{indent}# {code}\n" if not line.endswith('\n') else f"{indent}# {code}\n"
            new_lines.append(new_line)
            modified = True
            commented_count += 1
            if dry_run:
                print(f"  [Preview] Will comment line: {line.strip()[:80]}")
            continue
        
        # Try to match other webm containing code
        match = webm_pattern.match(line)
        if match and ('movie_cutscene' in line or 'Video' in line or 'Movie' in line):
            new_line = f"# {line}" if not line.startswith('#') else line
            new_lines.append(new_line)
            modified = True
            commented_count += 1
            if dry_run:
                print(f"  [Preview] Will comment line: {line.strip()[:80]}")
            continue
        
        new_lines.append(line)
    
    if modified and not dry_run:
        try:
            with open(rpy_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  Commented {commented_count} lines of webm related code")
        except Exception as e:
            print(f"  Error: Cannot write file {rpy_file}: {e}")
            return False, True
    
    return modified, False


def uncomment_webm_lines(rpy_file, dry_run=False):
    """Uncomment lines containing webm (restore mode)
    Returns: (modified, error) - modified is True if changes were made, error is True if an error occurred
    """
    try:
        with open(rpy_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines(keepends=True)
    except Exception as e:
        print(f"  Error: Cannot read file {rpy_file}: {e}")
        return False, True
    
    modified = False
    new_lines = []
    uncommented_count = 0
    
    # Match commented out webm related lines
    commented_pattern = re.compile(r'^(\s*)#\s*(.*\.webm.*)', re.IGNORECASE)
    
    for line in lines:
        match = commented_pattern.match(line)
        if match and ('movie_cutscene' in line or 'Video' in line or 'Movie' in line):
            indent = match.group(1)
            code = match.group(2)
            # Strip line ending before adding to avoid duplication
            code = code.rstrip('\n\r')
            new_line = f"{indent}{code}\n"
            new_lines.append(new_line)
            modified = True
            uncommented_count += 1
            if dry_run:
                print(f"  [Preview] Will restore line: {new_line.strip()[:80]}")
        else:
            new_lines.append(line)
    
    if modified and not dry_run:
        try:
            with open(rpy_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  Restored {uncommented_count} lines of webm related code")
        except Exception as e:
            print(f"  Error: Cannot write file {rpy_file}: {e}")
            return False, True
    
    return modified, False


def delete_webm_files(webm_files, dry_run=False):
    """Delete webm files"""
    deleted = []
    for webm_path in webm_files:
        if dry_run:
            print(f"  [Preview] Will delete: {webm_path}")
            deleted.append(webm_path)
        else:
            try:
                webm_path.unlink()
                print(f"  Deleted: {webm_path}")
                deleted.append(webm_path)
            except Exception as e:
                print(f"  Error: Cannot delete {webm_path}: {e}")
    return deleted


def main():
    parser = argparse.ArgumentParser(
        description='Adaptive WebM file cleanup tool - Automatically scan and process webm files in project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remove_op.py              # Default mode: scan and cleanup
  python remove_op.py --dry-run    # Preview mode: only show operations to be performed
  python remove_op.py --restore    # Restore mode: uncomment webm related code
  python remove_op.py --scan-only  # Scan only: show discovered webm files and references
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview mode: show operations to be performed without executing')
    parser.add_argument('--restore', action='store_true',
                        help='Restore mode: uncomment webm related code (restore original state)')
    parser.add_argument('--scan-only', action='store_true',
                        help='Only scan and report, no modifications')
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    print("=" * 60)
    
    has_error = False
    
    # 1. Scan webm files
    print("\n[1/3] Scanning webm files...")
    webm_files = find_webm_files(project_root)
    
    if not webm_files:
        print("  No .webm files found")
    else:
        print(f"  Found {len(webm_files)} .webm file(s):")
        for f in webm_files:
            size = f.stat().st_size if f.exists() else 0
            print(f"    - {f.relative_to(project_root)} ({size/1024/1024:.2f} MB)")
    
    if args.scan_only:
        # Scan only mode: also show code references
        print("\n[2/3] Scanning script references...")
        rpy_files = find_rpy_files(project_root)
        webm_names = [f.name for f in webm_files]
        
        found_refs = False
        for rpy_file in rpy_files:
            refs = find_webm_references(rpy_file, webm_names)
            if refs:
                if not found_refs:
                    print("  Found webm references:")
                    found_refs = True
                print(f"    File: {rpy_file.relative_to(project_root)}")
                for line_num, line, is_movie in refs:
                    prefix = "[movie_cutscene]" if is_movie else ""
                    print(f"      Line {line_num}: {line.strip()[:60]}{prefix}")
        
        if not found_refs:
            print("  No webm references found in scripts")
        
        print("\n[Scan complete]")
        return True
    
    # 2. Process script files
    print("\n[2/3] Processing script files...")
    rpy_files = find_rpy_files(project_root)
    modified_files = []
    
    for rpy_file in rpy_files:
        if args.restore:
            result, error = uncomment_webm_lines(rpy_file, dry_run=args.dry_run)
            if error:  # Error occurred
                has_error = True
            elif result:  # Successfully modified
                modified_files.append(rpy_file)
                if args.dry_run:
                    print(f"  {rpy_file.relative_to(project_root)} (preview)")
                else:
                    print(f"  Restored: {rpy_file.relative_to(project_root)}")
        else:
            result, error = comment_webm_lines(rpy_file, dry_run=args.dry_run)
            if error:  # Error occurred
                has_error = True
            elif result:  # Successfully modified
                modified_files.append(rpy_file)
                if args.dry_run:
                    print(f"  {rpy_file.relative_to(project_root)} (preview)")
                else:
                    print(f"  Modified: {rpy_file.relative_to(project_root)}")
    
    if not modified_files and not has_error:
        print("  No script files need modification")
    
    # 3. Process webm files (only in non-restore mode)
    if not args.restore:
        print("\n[3/3] Processing webm files...")
        if webm_files:
            if args.dry_run:
                print("  [Preview] Following files will be deleted:")
                for f in webm_files:
                    print(f"    - {f.relative_to(project_root)}")
            else:
                deleted = delete_webm_files(webm_files, dry_run=False)
                if len(deleted) != len(webm_files):
                    has_error = True
                print(f"  Deleted {len(deleted)} file(s)")
        else:
            print("  No webm files to delete")
    
    # Summary
    print("\n" + "=" * 60)
    if args.dry_run:
        print("[Preview mode complete] No actual modifications made")
    elif args.restore:
        if has_error:
            print(f"[Restore complete with errors] Restored {len(modified_files)} file(s)")
        else:
            print(f"[Restore complete] Restored {len(modified_files)} file(s)")
    else:
        if has_error:
            print(f"[Cleanup complete with errors] Modified {len(modified_files)} script(s), deleted {len(webm_files)} webm file(s)")
        else:
            print(f"[Cleanup complete] Modified {len(modified_files)} script(s), deleted {len(webm_files)} webm file(s)")
    
    return not has_error


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
