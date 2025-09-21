import os
import time
import subprocess
import threading

SCRIPT = './flash_software.sh'
OUTPUT_PRE = 'flash_software'

os.makedirs('output', exist_ok=True)


def flash_board(path):
    with open(os.path.join('output', f'{OUTPUT_PRE}_{path.replace('/', '_')}.out'), 'wb') as f:
        print(f'flashing {path} (stdout,stderr > {f.name})')
        p = subprocess.Popen([SCRIPT, path], stdout=f, stderr=f, bufsize=0)
        p.wait()
        flashing.remove(path)
        print(f'done flashing {path}')


connected = set()
flashing = set()

while True:
    for file in os.listdir('/dev'):
        if file.startswith('cu.usb'):
            path = os.path.join('/dev', file)
            if path not in connected:
                print(f'detected {path}')
                connected.add(path)
                flashing.add(path)
                threading.Thread(target=flash_board, args=[path]).start()

    # for some reason, after flashing, it disappears from /dev/ and then reappears, so have to manually restart script
    # to_remove = []
    # for path in connected:
    #     if not os.path.exists(path):
    #         print(f'no longer detected {path}')
    #         to_remove.append(path)
    # for path in to_remove:
    #     connected.remove(path)

    print(f'still flashing: {flashing}')
    time.sleep(1)
