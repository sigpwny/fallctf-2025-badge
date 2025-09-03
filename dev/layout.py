import time
from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display
    from view import View


class Layout:
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

    def render(self):
        self._renders_count += 1


class SimpleLayout(Layout):
    def __init__(self, display, view):
        # type: (Display | None, View) -> None
        super().__init__(display)
        self.view = view

    def first_render(self, *args, **kwargs):
        self.view.first_render(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.view.update(*args, **kwargs)

    def render(self):
        super().render()
        self.display.clear()
        self.view.render()
        self.display.show()


class ColumnLayout(Layout):
    def __init__(self, display, *columns, cols_count=-1, col_width=-1, y=0):
        # type: (Display | None, *View, int, int, int) -> None
        """
        cols_count: number of columns, -1 to auto-detect
        col_width: width of each column, -1 to auto-detect
        y: y position of the columns
        """
        super().__init__(display)
        self.columns: list[View | None] = list(columns)
        if cols_count == -1 and col_width == -1:
            self.col_width = display.width // len(columns)
            self.cols_count = len(columns)
        elif cols_count == -1:
            self.col_width = col_width
            self.cols_count = display.width // col_width
        elif col_width == -1:
            self.cols_count = cols_count
            self.col_width = display.width // cols_count
        else:
            self.cols_count = cols_count
            self.col_width = col_width
        if len(columns) > self.cols_count:
            self.columns = columns[: self.cols_count]
        elif len(columns) < self.cols_count:
            self.columns.extend([None] * (self.cols_count - len(columns)))
        self.y = y

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
        self.display.show()
