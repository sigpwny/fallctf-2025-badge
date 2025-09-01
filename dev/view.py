import time
from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


class View:
    def __init__(self, display):
        # type: (Display | None) -> None
        self.display = display
        self.start = time.time_ns()
        self._renders_count = 0

    def get_renders_per_second(self):
        elapsed = time.time_ns() - self.start
        if elapsed == 0:
            return 0
        return self._renders_count / (elapsed / 1e9)

    def update(self, data):
        pass

    def render(self):
        self._renders_count += 1


class BasicTextView(View):
    def __init__(self, display):
        super().__init__(display)
        num_lines = self.display.height // self.display.line_height
        self.lines = ["" for _ in range(num_lines)]

    def update(self, index, line):
        if 0 <= index < len(self.lines):
            self.lines[index] = line
        else:
            raise IndexError("Line index out of range")

    def first_render(self):
        self.render(refresh_all=True)

    def render(self, refresh_all=False):
        super().render()
        self.display.clear()
        for i, line in enumerate(self.lines):
            self.display.draw_text(0, i * self.display.line_height, line)
        self.display.show()


class FontTextView(View):
    def __init__(
        self,
        display,
        font_path: str,
        cache_index=False,
        color=None,
        x_spacing=1,
        y_spacing=1,
        rot=0,
    ):
        # type: (Display, str, bool, int|None, int, int, int) -> None
        super().__init__(display)
        self.color = color if color is not None else self.display.display.tft.WHITE
        from microfont import MicroFont

        self.font = MicroFont(font_path, cache_index=cache_index)
        self.data = ""
        self.x = 0
        self.y = 0
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing
        self.rot = rot

    def update(self, x, y, data: str):
        self.x = x
        self.y = y
        self.data = data

    def setColor(self, color):
        self.color = color

    def setRotation(self, rot):
        self.rot = rot

    def setSpacing(self, x_spacing, y_spacing):
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing

    def render(self):
        super().render()
        self.display.clear()
        self.font.write(
            self.data,
            self.display.display,
            1,
            self.display.display.width,
            self.display.display.height,
            self.x,
            self.y,
            self.color,
            y_spacing=self.y_spacing,
            x_spacing=self.x_spacing,
            rot=self.rot,
        )
        self.display.show()
