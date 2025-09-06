#!/usr/bin/env python3

from env import Environment
import sys

try:
    import os
    if 'environ' in dir(os):
        BOARDLESS_MODE = os.environ.get('BOARDLESS_MODE', '0') == '1'
    else:
        BOARDLESS_MODE = False
except ImportError:
    BOARDLESS_MODE = False


def main():
    env = Environment(mode='dev', boardless_mode=BOARDLESS_MODE)

    try:
        env.run()
    except KeyboardInterrupt as e:
        sys.print_exception(e)
        print("Exiting...")


if __name__ == '__main__':
    main()
