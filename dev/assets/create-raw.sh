#!/usr/bin/env bash

python3 -c "from PIL import Image; import struct, os; [open(os.path.splitext(f)[0]+'.raw','wb').write(b''.join(struct.pack('>H',((r&0xF8)<<8)|((g&0xFC)<<3)|(b>>3)) for y in range(Image.open(f).convert('RGB').height) for x in range(Image.open(f).convert('RGB').width) for r,g,b in [Image.open(f).convert('RGB').getpixel((x,y))])) for f in os.listdir('.') if f.lower().endswith('.png')]"
