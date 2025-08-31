from logger import log
from font_writer import CWriter, Writer

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


class View:
    def __init__(self, display):
        # type: (Display | None) -> None
        self.display = display

    def update(self, data):
        pass

    def render(self):
        pass


class BasicTextView(View):
    def __init__(self, display=None, num_lines=5):
        # type: (Display | None, int) -> None
        super().__init__(display)
        self.lines = ["" for _ in range(num_lines)]

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


class FontTextView(View):
    def __init__(self, display, font_path: str, fgcolor=None, bgcolor=None, inv=False):
        # type: (Display, str, int | None, int | None, bool) -> None
        super().__init__(display)
        self.writer = CWriter(
            self.display.display,
            __import__(font_path),
            fgcolor=fgcolor,
            bgcolor=bgcolor,
        )
        self.inv = inv
        self.data = ""
        self.x = 0
        self.y = 0

    def update(self, x, y, data: str):
        self.x = x
        self.y = y
        self.data = data

    def setColor(self, fgcolor, bgcolor):
        self.writer.setcolor(fgcolor, bgcolor)

    def setInvert(self, invert):
        self.inv = invert

    def render(self):
        self.display.clear()
        Writer.set_textpos(self.display.display, self.x, self.y)
        self.writer.printstring(self.data, invert=self.inv)
        self.display.show()
