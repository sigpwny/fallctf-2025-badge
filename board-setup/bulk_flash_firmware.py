import os
import time
import subprocess
import threading

SCRIPT = './flash_firmware.sh'
OUTPUT_PRE = 'flash_firmware'

os.makedirs('output', exist_ok=True)


def flash_board(path):
    with open(os.path.join('output', f'{OUTPUT_PRE}_{path.replace('/', '_')}.out'), 'wb') as f:
        print(f'flashing {path} (stdout,stderr > {f.name})')
        p = subprocess.Popen([SCRIPT, path], stdout=f, stderr=f, bufsize=0)
        p.wait()
        print(f'done flashing {path}')


flashing = set()

while True:
    for file in os.listdir('/dev'):
        if file.startswith('cu.usb'):
            path = os.path.join('/dev', file)
            if path not in flashing:
                print(f'detected {path}')
                flashing.add(path)
                threading.Thread(target=flash_board, args=[path]).start()

    to_remove = []
    for path in flashing:
        if not os.path.exists(path):
            print(f'no longer detected {path}')
            to_remove.append(path)
    for path in to_remove:
        flashing.remove(path)

    time.sleep(1)
