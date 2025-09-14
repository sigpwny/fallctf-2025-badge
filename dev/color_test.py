from view import View
import math

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


def hsv_to_rgb(h, s, v):
    if s == 0.0:
        v *= 255
        return (int(v), int(v), int(v))
    i = int(h * 6.0)  # assume int() truncates!
    f = (h * 6.0) - i
    p = int(255 * v * (1.0 - s))
    q = int(255 * v * (1.0 - s * f))
    t = int(255 * v * (1.0 - s * (1.0 - f)))
    v = int(255 * v)
    i = i % 6
    if i == 0:
        return (v, t, p)
    if i == 1:
        return (q, v, p)
    if i == 2:
        return (p, v, t)
    if i == 3:
        return (p, q, v)
    if i == 4:
        return (t, p, v)
    if i == 5:
        return (v, p, q)


class ColorTest(View):
    def __init__(self, display, width=-1, height=0):
        # type: (Display, int, int) -> None
        super().__init__(display)
        self.display = display
        self.width = width if width > 0 else display.display.width
        self.height = height if height > 0 else display.display.height
        self.x = 0
        self.y = 0

    def render_x_y(self, x, y):
        self.x = x
        self.y = y
        self.render()

    def render(self):
        # init area with black
        self.display.display.fill_rect(self.x, self.y, self.width, self.height, self.display.display.tft.BLACK)
        # draw color bars that take up the full height
        num_colors = 20
        colors = [self.display.display.tft.color(*hsv_to_rgb(i / num_colors, 1, 1)) for i in range(num_colors)]
        bar_width = self.width // len(colors)
        for i, color in enumerate(colors):
            x = i * bar_width
            self.display.display.fill_rect(self.x + x, self.y, bar_width, self.height, color)
        self.display.display.show()
