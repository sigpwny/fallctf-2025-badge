import time
from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display
    from view import View


class Layout:
    def __init__(self, display):
        # type: (Display) -> None
        self.display = display
        self.start = time.time_ns()
        self._renders_count = 0

    def get_renders_per_second(self):
        elapsed = time.time_ns() - self.start
        if elapsed == 0:
            return 0
        return self._renders_count / (elapsed / 1e9)

    def render(self):
        self._renders_count += 1


class SimpleLayout(Layout):
    def __init__(self, display, view, x=0, y=0, draw_outline=False, outline_color=None):
        # type: (Display, View, int, int, bool, int | None) -> None
        super().__init__(display)
        self.view = view
        self.x = x
        self.y = y
        self.draw_outline = draw_outline
        self.outline_color = outline_color or self.display.display.tft.GREEN

    def first_render(self, *args, **kwargs):
        self.view.first_render(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.view.update(*args, **kwargs)

    def render(self):
        super().render()
        self.display.clear()
        self.view.render_x_y(self.x, self.y)
        if self.draw_outline:
            w, h = self.view.get_width_height()
            self.display.display.rect(
                self.x, self.y, self.x + w, self.y + h, self.outline_color, False
            )
        self.display.show()

# no dataclass in micropython
# @dataclass
class Style:
    # one bit for x and y, 0 = absolute, 1 = relative
    posType: int = 0b11
    # if type is ABSOLUTE, x,y is position
    # if type is RELATIVE, x,y is padding from previous element
    x: int = 0
    y: int = 0
    hidden: bool = False
    draw_outline: bool = False
    outline_color: int | None = None

    def __init__(
        self,
        posType: int = 0b11,
        x: int = 0,
        y: int = 0,
        hidden: bool = False,
        draw_outline: bool = False,
        outline_color: int | None = None,
    ):
        self.posType = posType
        self.x = x
        self.y = y
        self.hidden = hidden
        self.draw_outline = draw_outline
        self.outline_color = outline_color


class ComplexLayout(Layout):
    def __init__(self, display, *views, x=0, y=0):
        # type: (Display, *tuple[View, Style], int, int) -> None
        super().__init__(display)
        self.views: list[tuple[View, Style]] = list(views)
        self.x = x
        self.y = y

    def __len__(self):
        return len(self.views)

    def first_render(self, *args, **kwargs):
        for v, s in self.views:
            if not s.hidden:
                v.first_render(*args, **kwargs)

    def __setitem__(self, index: int, view_style):
        # type: (int, tuple[View, Style]) -> None
        self.views[index] = view_style

    def __getitem__(self, index: int):
        # type: (int) -> tuple[View, Style]
        return self.views[index]

    def append(self, view_style):
        # type: (tuple[View, Style]) -> None
        self.views.append(view_style)

    def render(self):
        super().render()
        self.display.clear()
        cur_x = self.x
        cur_y = self.y
        for v, s in self.views:
            if not s.hidden:
                if s.posType & 0b01:
                    # relative y
                    cur_y += s.y
                else:
                    cur_y = self.y + s.y
                if s.posType & 0b10:
                    # relative x
                    cur_x += s.x
                else:
                    cur_x = self.x + s.x
                v.render_x_y(cur_x, cur_y)
                w, h = v.get_width_height()
                if s.draw_outline:
                    self.display.display.rect(
                        cur_x,
                        cur_y,
                        cur_x + w,
                        cur_y + h,
                        s.outline_color or self.display.display.tft.GREEN,
                        False,
                    )
                cur_x += w
                cur_y += h
        self.display.show()
