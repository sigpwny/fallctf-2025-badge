import time
from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display
    from soft_display import SoftDisplay
    from view import View


class Layout:
    def __init__(self, display):
        # type: (Display | SoftDisplay | None) -> None
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
        # type: (Display | SoftDisplay | None, View, int, int, bool, int) -> None
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


class ColumnLayout(Layout):
    def __init__(
        self,
        display,
        *columns,
        cols_count=-1,
        col_width=-1,
        y=0,
        fixed_width=-1,
        draw_outline=False,
        outline_color=None
    ):
        # type: (Display | SoftDisplay | None, *View, int, int, int, int, bool, int) -> None
        """
        cols_count: number of columns, -1 to auto-detect
        col_width: width of each column, -1 to auto-detect
        y: y position of the columns
        """
        super().__init__(display)
        self.columns: list[View | None] = list(columns)
        self.cols_count = len(columns) if cols_count == -1 else cols_count
        w = fixed_width if fixed_width != -1 else display.width
        self.col_width = w // self.cols_count if col_width == -1 else col_width
        if len(columns) > self.cols_count:
            self.columns = columns[: self.cols_count]
        elif len(columns) < self.cols_count:
            self.columns.extend([None] * (self.cols_count - len(columns)))
        self.y = y
        self.draw_outline = draw_outline
        self.outline_color = outline_color or self.display.display.tft.GREEN

    def first_render(self, *args, **kwargs):
        for v in self.columns:
            if v is not None:
                v.first_render(*args, **kwargs)

    def __setitem__(self, index: int, view):
        # type: (int, View) -> None
        self.columns[index] = view

    def __getitem__(self, index: int):
        # type: (int) -> View | None
        return self.columns[index]

    def render(self):
        super().render()
        self.display.clear()
        for i, v in enumerate(self.columns):
            if v is not None:
                v.render_x_y(i * self.col_width, self.y)
        if self.draw_outline:
            width = 0
            max_h = 0
            for v in self.columns:
                if v is not None:
                    w, h = v.get_width_height()
                    width = w
                    max_h = max(max_h, h)
            self.display.display.rect(
                0,
                self.y,
                self.col_width * (len(self.columns) - 1) + width,
                max_h,
                self.outline_color,
                False,
            )

        self.display.show()
