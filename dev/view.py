import time
from logger import log
from framebuf import FrameBuffer, MONO_HMSB, RGB565
from boolpalette import BoolPalette

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


class View:
    _changed = True
    _cache_x_y = (0, 0)
    _cache_w_h = (0, 0)

    def __init__(self, display):
        # type: (Display) -> None
        self.display = display
        self.start = time.time_ns()
        self._renders_count = 0

    def update(self, *data):
        pass

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if not self._changed:
            self._changed = True

    def render(self):
        pass

    def render_x_y(self, x, y):
        pass

    def render_x_y_cache(self, x, y, enable_render_cache=False):
        if not enable_render_cache:
            self.render_x_y(x, y)
        else:
            if self._cache_x_y != (x, y) or self._changed:
                # ensure expected black background
                self.display.display.fill_rect(
                    self._cache_x_y[0],
                    self._cache_x_y[1],
                    self._cache_w_h[0],
                    self._cache_w_h[1],
                    0,
                )
                self.render_x_y(x, y)
                self._cache_x_y = (x, y)
                self._cache_w_h = self.get_width_height()
                self._changed = False

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
        super().first_render()
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
        if self.format == RGB565:
            # # write into self.display.display.buffer directly
            # for py in range(self.height):
            #     for px in range(self.width):
            #         pixel = self.bitmap.pixel(px, py)
            #         self.display.display.pixel(self.x + px, self.y + py, pixel)
            self.display.display.blit(self.bitmap, self.x, self.y, -1)
        else:
            self.display.display.blit(self.bitmap, self.x, self.y, -1, self.palette)

    def get_width_height(self):
        return self.width, self.height


class PBar(View):
    def __init__(
        self,
        display,
        capacity,
        initial_value=0,
        # theme=0,
        width=100,
        height=10,
        direction=0,  # 0: horizontal, 1: vertical
        fg_color=None,
        text_mode=0,  # 0: no text, 1: value, 2: changes from initial value
    ):
        # type: (Display, int, int, int, int, int, int|None, int) -> None
        super().__init__(display)
        self.capacity = capacity
        if text_mode == 2:
            self.i_val = initial_value
        self.value = initial_value
        # self.theme = theme
        self.width = width
        self.height = height
        self.fg_color = (
            fg_color if fg_color is not None else self.display.display.tft.WHITE
        )
        self.shake_color = self.display.display.tft.RED
        self.direction = direction
        self.shake_notice = 0
        self.text_mode = text_mode
        self.text = ""
        if self.text_mode == 1:
            self.text = f"{self.value}"
        elif self.text_mode == 2:
            self.text = f"+0"

    def update(self, value):
        if 0 <= value <= self.capacity:
            self.value = value
            return 0
        else:
            return -1

    def set_color(self, color):
        self.fg_color = color

    def shake(self, color=None, time=2):
        if color is not None:
            self.shake_color = color
        self.shake_notice = time

    def get_width_height(self):
        return self.width + len(self.text) * self.display.char_width + 5 + 1, self.height

    def render_x_y(self, x, y):
        self.x = x
        self.y = y
        self.render()

    def render(self):
        super().render()
        # default theme like a health bar with border. If shake_notice > 0, draw a red border
        if self.shake_notice > 0:
            self.shake_notice -= 1
            border_color = self.shake_color
        else:
            border_color = self.fg_color
        self.display.display.rect(self.x, self.y, self.width, self.height, border_color)
        if self.direction == 0:
            fill_width = int(self.width * self.value / self.capacity)
            self.display.display.fill_rect(
                self.x + 1, self.y + 1, fill_width - 2, self.height - 2, self.fg_color
            )
            self.display.display.fill_rect(
                self.x + 1 + fill_width,
                self.y + 1,
                self.width - 2 - fill_width,
                self.height - 2,
                self.display.display.tft.BLACK,
            )
        else:
            fill_height = int(self.height * self.value / self.capacity)
            self.display.display.fill_rect(
                self.x + 1,
                self.y + self.height - fill_height + 1,
                self.width - 2,
                fill_height - 2,
                self.fg_color,
            )
            self.display.display.fill_rect(
                self.x + 1,
                self.y + 1,
                self.width - 2,
                self.height - 2 - fill_height,
                self.display.display.tft.BLACK,
            )
        # draw number after whole bar in right
        if self.text_mode == 1:
            self.text = f"{self.value}"
        elif self.text_mode == 2:
            self.text = f"{self.value - self.i_val:+d}"
        self.display.draw_text(
            self.x + self.width + 5,
            self.y + (self.height - self.display.line_height) // 2,
            self.text,
        )
