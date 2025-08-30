from logger import log


class View:
    def __init__(self, display):
        self.display = display

    def update(self, data):
        pass

    def render(self):
        pass


class BasicTextView(View):
    def __init__(self, display=None, num_lines=5):
        super().__init__(display)
        self.lines = ['' for _ in range(num_lines)]

    def update(self, index, line):
        if 0 <= index < len(self.lines):
            self.lines[index] = line
        else:
            raise IndexError("Line index out of range")

    def first_render(self):
        self.render(refresh_all=True)

    def render(self, refresh_all=False):
        self.display.clear()
        for i, line in enumerate(self.lines):
            self.display.draw_text(0, i * self.display.line_height, line)
        self.display.show()

