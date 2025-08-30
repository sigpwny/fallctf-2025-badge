import asyncio
from logger import log


class SoftDisplay:
    def __init__(self):
        self.width = 160
        self.height = 128
        self.line_height = 10
        # create a grid of spaces to represent the display
        self._font_width = 5
        self._text_buffer = [[' ' for _ in range(self.width // self._font_width)] for _ in range(self.height // self.line_height)]
        self._display_file_name = 'soft_display.txt'
        log(f'Monitor the soft display using the command "watch -n1 cat {self._display_file_name}"')

    def clear(self):
        self._text_buffer = [[' ' for _ in range(self.width // self._font_width)] for _ in range(self.height // self.line_height)]

    def draw_text(self, x, y, text):
        row = y // self.line_height
        col = x // self._font_width
        for i, char in enumerate(text):
            if 0 <= row < len(self._text_buffer) and 0 <= col + i < len(self._text_buffer[0]):
                self._text_buffer[row][col + i] = char

    def show(self):
        with open(self._display_file_name, 'w') as f:
            f.write('-' * (self.width // self._font_width + 2) + '\n')
            for line in self._text_buffer:
                f.write('|')
                f.write(''.join(line))
                f.write('|\n')
            f.write('-' * (self.width // self._font_width + 2) + '\n')

    async def run(self):
        pass
