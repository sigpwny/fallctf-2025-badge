#!/usr/bin/env python3

# for each png in this file, convert it to RGB565 raw format and write it to <name>.raw

import os
from PIL import Image
import struct
import glob
import sys
import errno
import time

def convert_image_to_rgb565_raw(image_path, output_path):
    # Open the image using PIL
    with Image.open(image_path) as img:
        # Convert image to RGB if it's not in that mode
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.thumbnail((160, 128))
        
        # Create a new image with a black background
        new_img = Image.new('RGB', (160, 128), (0, 0, 0))
        new_img.paste(img, ((160 - img.width) // 2, (128 - img.height) // 2))
        
        # Convert to RGB565
        rgb565_data = bytearray()
        for y in range(new_img.height):
            for x in range(new_img.width):
                r, g, b = new_img.getpixel((x, y))
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                rgb565_data += struct.pack('>H', rgb565)
        
        # Write the raw data to output file
        with open(output_path, 'wb') as f:
            f.write(rgb565_data)
    
    print(f"Converted {image_path} to {output_path}")

def main():
    input_folder = 'assets'
    output_folder = 'assets'
    
    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    
    png_files = glob.glob(os.path.join(input_folder, '*.png'))
    
    if not png_files:
        print("No PNG files found in the assets directory.")
        return
    
    for png_file in png_files:
        base_name = os.path.splitext(os.path.basename(png_file))[0]
        raw_file = os.path.join(output_folder, f"{base_name}.raw")
        convert_image_to_rgb565_raw(png_file, raw_file)
        time.sleep(0.1)  # Small delay to avoid overwhelming the system

if __name__ == "__main__":
    main()
