import time
from logger import log
from framebuf import FrameBuffer, MONO_HMSB, RGB565
from boolpalette import BoolPalette

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


class View:
    def __init__(self, display):
        # type: (Display) -> None
        self.display = display
        self.start = time.time_ns()
        self._renders_count = 0

    def update(self, *data):
        pass

    def render(self):
        pass

    def render_x_y(self, x, y):
        pass

    def get_width_height(self) -> tuple[int, int]:
        return 0, 0

    def first_render(self):
        self.render()


class BasicTextView(View):
    def __init__(self, display):
        super().__init__(display)
        self.max_line = self.display.height // self.display.line_height
        self.lines = []

    def update(self, index, line):
        if 0 <= index < self.max_line:
            if index >= len(self.lines):
                self.lines.extend([""] * (index + 1 - len(self.lines)))
            self.lines[index] = line
        else:
            raise IndexError("Line index out of range")

    def first_render(self):
        self.render(refresh_all=True)

    def render(self, refresh_all=False):
        super().render()
        for i, line in enumerate(self.lines):
            self.display.draw_text(0, i * self.display.line_height, line)

    def render_x_y(self, x, y):
        super().render()
        for i, line in enumerate(self.lines):
            self.display.draw_text(x, y + i * self.display.line_height, line)

    def get_width_height(self):
        return (
            max(len(line) for line in self.lines) * self.display.char_width,
            len(self.lines) * self.display.line_height,
        )


class FontTextView(View):
    def __init__(
        self,
        display,
        font_path,
        data: str = "",
        cache_index=False,
        color=None,
        x_spacing=1,
        y_spacing=1,
        rot=0,
    ):
        # type: (Display, str, str, bool, int|None, int, int, int) -> None
        super().__init__(display)
        self.color = color if color is not None else self.display.display.tft.WHITE
        from microfont import MicroFont

        self.font = MicroFont(font_path, cache_index=cache_index)
        self.data = ""
        self.x = 0
        self.y = 0
        self.x_pad = 0
        self.y_pad = 0
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing
        self.rot = rot
        self.data = data

    def update(self, x, y, data: str):
        self.x_pad = x
        self.y_pad = y
        self.data = data

    def setColor(self, color):
        self.color = color

    def setRotation(self, rot):
        self.rot = rot

    def setSpacing(self, x_spacing, y_spacing):
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing

    def render_x_y(self, x, y):
        self.x = x
        self.y = y
        self.render()

    def render(self):
        super().render()
        self.font.write(
            self.data,
            self.display.display.buffer,
            1,
            self.display.display.width,
            self.display.display.height,
            self.x + self.x_pad,
            self.y + self.y_pad,
            self.color,
            y_spacing=self.y_spacing,
            x_spacing=self.x_spacing,
            rot=self.rot,
        )

    def get_width_height(self):
        lines = self.data.split("\n")
        return (
            self.x_pad
            + max(len(line) for line in lines) * (self.font.max_width + self.x_spacing)
            - self.x_spacing,
            self.y_pad
            + len(lines) * (self.font.height + self.y_spacing)
            - self.y_spacing,
        )


class BitMapView(View):
    def __init__(
        self,
        display,
        bitmap,
        width,
        height,
        x=0,
        y=0,
        format=MONO_HMSB,
        fg_color=None,
        bg_color=None,
    ):
        # type: (Display, bytearray, int, int, int, int, int, int|None, int|None) -> None
        super().__init__(display)
        self.bitmap = FrameBuffer(bitmap, width, height, format)
        self.x = x
        self.y = y
        self.palette = BoolPalette(RGB565)
        self.width = width
        self.height = height
        if fg_color is not None:
            self.palette.fg(fg_color)
        else:
            self.palette.fg(self.display.display.tft.WHITE)
        if bg_color is not None:
            self.palette.bg(bg_color)
        else:
            self.palette.bg(self.display.display.tft.BLACK)
        self.format = format

    def set_colors(self, fg_color, bg_color):
        self.palette.fg(fg_color)
        self.palette.bg(bg_color)

    def update(self, bitmap, width, height, x=None, y=None, format=MONO_HMSB):
        self.bitmap = FrameBuffer(
            bitmap,
            width,
            height,
            format if format is not None else self.format,
        )
        self.width = width
        self.height = height
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y

    def render_x_y(self, x, y):
        self.x = x
        self.y = y
        self.render()

    def render(self):
        super().render()
        self.display.display.blit(self.bitmap, self.x, self.y, -1, self.palette)

    def get_width_height(self):
        return self.width, self.height
