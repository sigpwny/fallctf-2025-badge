#!/usr/bin/env python3

from env import Environment


def main():
    env = Environment(mode='dev')
    env.run()


if __name__ == '__main__':
    main()
