#!/usr/bin/env python3

from PIL import Image
import struct, os

FULL_SCREEN_LIST = ["first_page_1.png", "first_page_2.png", "first_page_3.png", "sponsors.png"]

def convert_fullscreen(image_path):
    # Open the image using PIL
    with Image.open(image_path) as img:
        # Convert image to RGB if it's not in that mode
        if img.mode != "RGB":
            img = img.convert("RGB")

        img.thumbnail((160, 128))

        # Create a new image with a black background
        new_img = Image.new("RGB", (160, 128), (0, 0, 0))
        new_img.paste(img, ((160 - img.width) // 2, (128 - img.height) // 2))

        # Convert to RGB565
        rgb565_data = bytearray()
        for y in range(new_img.height):
            for x in range(new_img.width):
                r, g, b = new_img.getpixel((x, y))
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                rgb565_data += struct.pack(">H", rgb565)

        # Write the raw data to output file
        with open(os.path.splitext(image_path)[0] + ".raw", "wb") as f:
            f.write(rgb565_data)


def convert_original_size(image_path):
    with open(os.path.splitext(image_path)[0] + ".raw", "wb") as f:
        img = Image.open(image_path).convert("RGB")
        f.write(
            b"".join(
                struct.pack(">H", ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3))
                for y in range(img.height)
                for x in range(img.width)
                for r, g, b in [img.getpixel((x, y))]
            )
        )


for f in os.listdir("."):
    if f.lower().endswith(".png"):
        if f in FULL_SCREEN_LIST:
            convert_fullscreen(f)
        else:
            convert_original_size(f)
