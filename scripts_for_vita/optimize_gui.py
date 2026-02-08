import os
import re
import shutil

# Get parent directory of script directory (project root)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
gui_path = os.path.join(base_dir, 'game', 'gui.rpy')
screens_path = os.path.join(base_dir, 'game', 'screens.rpy')

# Scale ratio (960 / 1280 = 0.75)
SCALE_RATIO = 0.75

# Config items that need fixed ratio scaling (current value -> calculate new value by ratio)
gui_numeric_configs = [
    # (config_name, should_scale)
    ('gui.textbox_height', True),
    ('gui.name_xpos', True),
    ('gui.name_ypos', True),
    ('gui.dialogue_xpos', True),
    ('gui.dialogue_ypos', True),
    ('gui.dialogue_width', True),
    ('gui.choice_button_width', True),
    ('gui.slot_button_width', True),
    ('gui.slot_button_height', True),
    ('config.thumbnail_width', True),
    ('config.thumbnail_height', True),
    ('gui.navigation_xpos', True),
    ('gui.skip_ypos', True),
    ('gui.notify_ypos', True),
    ('gui.choice_spacing', True),
    ('gui.navigation_spacing', True),
    ('gui.pref_spacing', True),
    ('gui.slot_spacing', True),
    ('gui.history_name_xpos', True),
    ('gui.history_name_ypos', True),
    ('gui.history_name_width', True),
    ('gui.history_text_xpos', False, lambda x: int(x * 0.5)),  # Move left more, give more space for text
    ('gui.history_text_ypos', True),
    ('gui.history_text_width', True),
    ('gui.nvl_name_width', True),
    ('gui.nvl_text_xpos', True),
    ('gui.nvl_text_ypos', True),
    ('gui.nvl_text_width', True),
    ('gui.nvl_thought_xpos', True),
    ('gui.nvl_thought_width', True),
    ('gui.nvl_button_xpos', True),
    ('gui.bar_size', True),
    ('gui.scrollbar_size', True),
    ('gui.slider_size', True),
    # Font sizes - slightly reduced but maintain readability
    ('gui.text_size', False, lambda x: max(18, int(x * 0.9))),
    ('gui.name_text_size', False, lambda x: max(22, int(x * 0.87))),
    ('gui.interface_text_size', False, lambda x: max(18, int(x * 0.9))),
    ('gui.label_text_size', False, lambda x: max(20, int(x * 0.9))),
    ('gui.notify_text_size', False, lambda x: max(14, int(x * 0.9))),
    ('gui.title_text_size', False, lambda x: max(40, int(x * 0.9))),
]

# Borders config (left, top, right, bottom)
gui_borders_configs = [
    'gui.namebox_borders',
    'gui.button_borders',
    'gui.radio_button_borders',
    'gui.check_button_borders',
    'gui.page_button_borders',
    'gui.quick_button_borders',
    'gui.choice_button_borders',
    'gui.slot_button_borders',
    'gui.frame_borders',
    'gui.confirm_frame_borders',
    'gui.skip_frame_borders',
    'gui.notify_frame_borders',
    'gui.bar_borders',
    'gui.scrollbar_borders',
    'gui.slider_borders',
    'gui.vbar_borders',
    'gui.vscrollbar_borders',
    'gui.vslider_borders',
    'gui.nvl_borders',
]

# Style configs in screens.rpy
screens_numeric_configs = [
    ('xsize 280', True),  # navigation_frame
    ('xsize 920', True),  # viewport
    ('top_padding 120', True),  # game_menu_outer_frame
    ('bottom_padding 30', True),
    ('left_margin 40', True),  # game_menu_content_frame
    ('right_margin 20', True),
]

def add_scroll_to_say_screen(file_path):
    """Add scrolling to say screen"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if scrolling already added
    if '# PS Vita: Add viewport for long text scrolling' in content:
        print("  say screen scroll already added, skipping")
        return 0
    
    # Find screen say definition (format should match actual file)
    old_text = 'text what id "what"'
    
    if old_text not in content:
        print("  say screen text area not found")
        return 0
    
    # Check if viewport already added
    if 'id "dialogue_viewport"' in content:
        print("  say screen scroll already added, skipping")
        return 0
    
    # Use two viewports for cases with/without side image, scale margins by ratio
    # Also override say_dialogue style xsize limit
    new_text = '''# PS Vita: Add viewport for long text scrolling
        if not isinstance(SideImage(), Null):
            viewport:
                id "dialogue_viewport"
                xpos int(gui.dialogue_xpos * 0.7)  # Reduce left margin
                xsize int(gui.dialogue_width * 1.2) - 90
                ypos int(gui.dialogue_ypos * 0.5)  # Reduce top margin
                ysize int((gui.textbox_height - gui.dialogue_ypos) * 0.9) - 5  # Reduce bottom margin
                
                scrollbars None
                mousewheel True
                draggable True
                
                text what id "what":
                    xsize None  # Override say_dialogue style xsize limit
        else:
            viewport:
                id "dialogue_viewport"
                xpos int(gui.dialogue_xpos * 0.7)  # Reduce left margin
                xsize int(gui.dialogue_width * 1.2)
                ypos int(gui.dialogue_ypos * 0.5)  # Reduce top margin
                ysize int((gui.textbox_height - gui.dialogue_ypos) * 0.9) - 5  # Reduce bottom margin
                
                scrollbars None
                mousewheel True
                draggable True
                
                text what id "what":
                    xsize None  # Override say_dialogue style xsize limit'''
    
    content = content.replace(old_text, new_text, 1)  # Only replace first occurrence
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  Added viewport scroll support to say screen")
    return 1

def backup_file(file_path):
    """Create backup file"""
    backup_path = file_path + '.backup'
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"Backup created: {backup_path}")
        return True
    else:
        print(f"Backup already exists: {backup_path}")
        return False

def restore_backup(file_path):
    """Restore file from backup"""
    backup_path = file_path + '.backup'
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        print(f"Restored from backup: {file_path}")
        return True
    return False

def scale_value(value, ratio=SCALE_RATIO):
    """Scale value by ratio"""
    return max(1, int(value * ratio))

def process_config_line(line, config_name, transform=None):
    """Process single line config, return new value or None"""
    # Match pattern: config_name = value
    pattern = rf'({re.escape(config_name)}\s*=\s*)(\d+)'
    match = re.search(pattern, line)
    if match:
        prefix = match.group(1)
        old_value = int(match.group(2))
        
        if transform:
            new_value = transform(old_value)
        else:
            new_value = scale_value(old_value)
        
        return line.replace(f'{prefix}{old_value}', f'{prefix}{new_value}'), old_value, new_value
    return None, None, None

def process_borders_line(line, config_name):
    """Process Borders config, return new value or None"""
    # Match pattern: config_name = Borders(left, top, right, bottom)
    pattern = rf'({re.escape(config_name)}\s*=\s*Borders\()(\d+),\s*(\d+),\s*(\d+),\s*(\d+)(\))'
    match = re.search(pattern, line)
    if match:
        prefix = match.group(1)
        left = int(match.group(2))
        top = int(match.group(3))
        right = int(match.group(4))
        bottom = int(match.group(5))
        suffix = match.group(6)
        
        new_left = scale_value(left)
        new_top = scale_value(top)
        new_right = scale_value(right)
        new_bottom = scale_value(bottom)
        
        old_str = f'{prefix}{left}, {top}, {right}, {bottom}{suffix}'
        new_str = f'{prefix}{new_left}, {new_top}, {new_right}, {new_bottom}{suffix}'
        
        return line.replace(old_str, new_str), (left, top, right, bottom), (new_left, new_top, new_right, new_bottom)
    return None, None, None

def process_screens_line(line, config_pattern, transform=None):
    """Process style configs in screens.rpy"""
    # Match pattern: keyword value
    pattern = rf'({re.escape(config_pattern.rsplit()[0])}\s+)(\d+)'
    match = re.search(pattern, line)
    if match:
        prefix = match.group(1)
        old_value = int(match.group(2))
        
        if transform:
            new_value = transform(old_value)
        else:
            new_value = scale_value(old_value)
        
        return line.replace(f'{prefix}{old_value}', f'{prefix}{new_value}'), old_value, new_value
    return None, None, None

def optimize_file(file_path, configs, is_screens=False, auto_restore=True):
    """Optimize single file"""
    if not os.path.exists(file_path):
        print(f"Error: File does not exist: {file_path}")
        return -1  # Return -1 to indicate error
    
    # Restore from backup if exists
    backup_path = file_path + '.backup'
    if auto_restore and os.path.exists(backup_path):
        restore_backup(file_path)
    
    # Create backup if not exists
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified_count = 0
    new_lines = []
    
    for line in lines:
        new_line = line
        modified = False
        
        # First try to process normal numeric configs
        for config in configs:
            if len(config) == 2:
                config_name, should_scale = config
                transform = None
            else:
                config_name, should_scale, transform = config
            
            if is_screens:
                result, old_val, new_val = process_screens_line(new_line, config_name, transform)
            else:
                result, old_val, new_val = process_config_line(new_line, config_name, transform)
            
            if result:
                new_line = result
                print(f"  {config_name}: {old_val} -> {new_val}")
                modified_count += 1
                modified = True
                break  # Only match one config per line
        
        # Then process Borders configs (gui.rpy only)
        if not modified and not is_screens:
            for borders_name in gui_borders_configs:
                result, old_vals, new_vals = process_borders_line(new_line, borders_name)
                if result:
                    new_line = result
                    print(f"  {borders_name}: Borders{old_vals} -> Borders{new_vals}")
                    modified_count += 1
                    modified = True
                    break
        
        new_lines.append(new_line)
    
    # Special handling: modify gui.init
    if not is_screens:
        content = ''.join(new_lines)
        if 'gui.init(1280, 720)' in content:
            content = content.replace('gui.init(1280, 720)', 'gui.init(960, 544)')
            print(f"  gui.init: 1280, 720 -> 960, 544")
            modified_count += 1
            new_lines = content.split('\n')
            new_lines = [line + '\n' for line in new_lines[:-1]] + [new_lines[-1]]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return modified_count

def optimize_gui(auto_restore=True):
    """Modify gui.rpy file, adjust GUI size for PS Vita screen"""
    print(f"\nProcessing: {gui_path}")
    print("-" * 40)
    count = optimize_file(gui_path, gui_numeric_configs, is_screens=False, auto_restore=auto_restore)
    if count < 0:
        print(f"Error: Failed to process gui.rpy")
        return -1
    print(f"Total {count} config(s) modified")
    return count

def optimize_screens(auto_restore=True):
    """Modify screens.rpy file, adjust viewport and navigation bar sizes"""
    print(f"\nProcessing: {screens_path}")
    print("-" * 40)
    count = optimize_file(screens_path, screens_numeric_configs, is_screens=True, auto_restore=auto_restore)
    if count < 0:
        print(f"Error: Failed to process screens.rpy")
        return -1
    
    # Add dialogue scroll support
    print("\n  [Extra] Adding dialogue scroll support...")
    scroll_count = add_scroll_to_say_screen(screens_path)
    if scroll_count > 0:
        count += scroll_count
    
    print(f"Total {count} config(s) modified")
    return count

def main():
    # Check for --no-restore argument
    auto_restore = '--no-restore' not in sys.argv
    
    print(f"=" * 50)
    print(f"GUI Optimization Tool - PS Vita Adaptation")
    print(f"=" * 50)
    print(f"Scale ratio: {SCALE_RATIO:.2f} (75%)")
    print(f"Target resolution: 960x544")
    if auto_restore:
        print(f"Mode: Auto-restore backup before modifying")
    else:
        print(f"Mode: Directly modify current file (no backup restore)")
    print(f"=" * 50)
    
    gui_count = optimize_gui(auto_restore=auto_restore)
    if gui_count < 0:
        print(f"\n" + "=" * 50)
        print(f"Processing failed!")
        print(f"=" * 50)
        return False
    
    screens_count = optimize_screens(auto_restore=auto_restore)
    if screens_count < 0:
        print(f"\n" + "=" * 50)
        print(f"Processing failed!")
        print(f"=" * 50)
        return False
    
    print(f"\n" + "=" * 50)
    print(f"Processing complete!")
    print(f"  gui.rpy: {gui_count} modification(s)")
    print(f"  screens.rpy: {screens_count} modification(s)")
    print(f"=" * 50)
    return True


if __name__ == "__main__":
    import sys
    main()
    sys.exit(0)
