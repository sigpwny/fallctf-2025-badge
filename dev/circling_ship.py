from view import View
import math

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


# TODO use ship icon UI instead of circle placeholder
class CirclingShip(View):
    def __init__(self, display, width=-1, height=0):
        # type: (Display, int, int) -> None
        super().__init__(display)
        self.display = display
        self.angle = 0
        self.trace = []  # Store previous positions
        self.trace_length = 15  # Number of trace points
        self.width = width if width > 0 else display.display.width
        self.height = height if height > 0 else display.display.height
        self.x = 0
        self.y = 0

    def render_x_y(self, x, y):
        self.x = x
        self.y = y
        self.render()

    def get_width_height(self):
        return self.width, self.height

    def render(self):
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        rx = self.width // 2 - 10  # Ellipse radius x
        ry = self.height // 2 - 10  # Ellipse radius y
        x = int(cx + rx * math.cos(math.radians(self.angle)))
        y = int(cy + ry * math.sin(math.radians(self.angle)))

        # Add current position to trace
        self.trace.append((x, y))
        if len(self.trace) > self.trace_length:
            self.trace.pop(0)

        # Draw trace with lightness change
        for i, (tx, ty) in enumerate(self.trace):
            size = 2 + (i * 3) // self.trace_length
            color = (
                self.display.display.tft.RED
                if i == len(self.trace) - 1
                else self.display.display.tft.GRAY
            )
            self.display.display.fill_circle(tx, ty, size, color)

        self.angle = (self.angle + 5) % 360
