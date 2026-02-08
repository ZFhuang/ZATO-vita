#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate system images for PSVita
- Generate icon0.png (128x128)
"""

import os
from PIL import Image


def crop_transparent(image):
    """Crop image to remove transparent areas"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Get alpha channel
    alpha = image.split()[-1]
    
    # Get bounding box of non-transparent pixels
    bbox = alpha.getbbox()
    
    if bbox:
        return image.crop(bbox)
    return image


def generate_icon0():
    """Generate icon0.png (128x128)"""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Source image path (relative to project root)
    src_path = os.path.join(os.path.dirname(script_dir), r"game\gui\window_icon.png")
    
    # Output directory and file (inside script directory)
    output_dir = os.path.join(script_dir, "sce_sys")
    output_path = os.path.join(output_dir, "icon0.png")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Open source image
    print(f"Processing: {src_path}")
    img = Image.open(src_path)
    
    # Remove transparent areas
    print("Removing transparent areas...")
    img = crop_transparent(img)
    
    # Resize to 128x128
    print("Resizing to 128x128...")
    img = img.resize((128, 128), Image.Resampling.LANCZOS)
    
    # Save
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")


def generate_startup():
    """Generate startup.png (280x158)"""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Source image path
    src_path = os.path.join(os.path.dirname(script_dir), r"game\images\logo\zatotitle.png")
    
    # Output directory and file
    output_dir = os.path.join(script_dir, "sce_sys", "livearea", "contents")
    output_path = os.path.join(output_dir, "startup.png")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Open source image
    print(f"Processing: {src_path}")
    img = Image.open(src_path)
    
    # Crop middle 85% area (remove black borders)
    width, height = img.size
    print(f"Original size: {width}x{height}")
    left = width * 0.075  # (1 - 0.85) / 2 = 0.075
    top = height * 0.075
    right = width * 0.925
    bottom = height * 0.925
    print("Cropping middle 85% area...")
    img = img.crop((left, top, right, bottom))
    
    # Resize to 280x158
    print("Resizing to 280x158...")
    img = img.resize((280, 158), Image.Resampling.LANCZOS)
    
    # Save
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")


def generate_bg_and_pic0():
    """Generate bg.png and pic0.png (960x544)"""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Source image path
    src_path = os.path.join(os.path.dirname(script_dir), r"game\gui\main_menu.png")
    
    # Output path 1: sce_sys/livearea/contents/bg.png
    output_dir1 = os.path.join(script_dir, "sce_sys", "livearea", "contents")
    output_path1 = os.path.join(output_dir1, "bg.png")
    
    # Output path 2: sce_sys/pic0.png
    output_dir2 = os.path.join(script_dir, "sce_sys")
    output_path2 = os.path.join(output_dir2, "pic0.png")
    
    # Create output directories
    os.makedirs(output_dir1, exist_ok=True)
    os.makedirs(output_dir2, exist_ok=True)
    
    # Open source image
    print(f"Processing: {src_path}")
    img = Image.open(src_path)
    
    # Original size 1280*720, crop bottom-right 1000*567 area
    # Top-left coordinates: (1280-1000, 720-567) = (280, 153)
    print("Cropping bottom-right 1000x567 area...")
    img_cropped = img.crop((280, 153, 1280, 720))
    
    # Resize to 960*544
    print("Resizing to 960x544...")
    img_resized = img_cropped.resize((960, 544), Image.Resampling.LANCZOS)
    
    # Save to both locations
    img_resized.save(output_path1, "PNG")
    print(f"Generated: {output_path1}")
    
    img_resized.save(output_path2, "PNG")
    print(f"Generated: {output_path2}")


if __name__ == "__main__":
    generate_icon0()
    generate_startup()
    generate_bg_and_pic0()
