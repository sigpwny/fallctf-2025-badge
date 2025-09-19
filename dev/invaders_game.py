import asyncio
import math
from array import array

from display import Display
from menu import Runnable
from view import BasicTextView, View
from layout import ComplexLayout, Style
from ST7735 import TFT

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


def rotate(x: float, y: float, cos: float, sin: float) -> tuple[float, float]:
    return (cos * x - sin * y,
            sin * x + cos * y)


class InvadersScreen(View):
    def __init__(self, display: Display, game: 'InvadersGame', width: int, height: int) -> None:
        super().__init__(display)
        self.game = game
        self.width = width
        self.height = height

    def render_x_y(self, x, y):
        x2 = self.display.width - 1
        y2 = self.display.height - 1

        # background
        self.display.display.line(x, y, x2, y, self.display.display.tft.WHITE)
        self.display.display.fill_rect(x, y + 1, x2, y2, (TFT.color(10, 7, 89)))

        # ship
        self.display.display.draw_circle(int(self.game.pos_x) + x, int(self.game.pos_y) + y, 5, self.display.display.tft.WHITE)
        points =\
            rotate(-4, -3, self.game.aim_x, self.game.aim_y) +\
            rotate(5, 0, self.game.aim_x, self.game.aim_y) +\
            rotate(-4, 3, self.game.aim_x, self.game.aim_y)
        ar = array('h', [int(x) for x in points])
        self.display.display.poly(int(self.game.pos_x) + x, int(self.game.pos_y) + y, ar, self.display.display.tft.RED, True)

        # bullets
        for pos_x, pos_y, _, _ in self.game.bullets:
            self.display.display.draw_circle(int(pos_x) + x, int(pos_y) + y, 1, self.display.display.tft.WHITE)

        # enemies
        for pos_x, pos_y, _, _, _ in self.game.enemies:
            self.display.display.draw_circle(int(pos_x) + x, int(pos_y) + y, 1, self.display.display.tft.GREEN)

    def get_width_height(self) -> tuple[int, int]:
        return (self.width, self.height)


class InvadersGame(Runnable):
    def __init__(self, device_io: 'DeviceIO') -> None:
        self.device_io = device_io

        self.speed = 5
        self.bullet_speed = 10

        self.view = ComplexLayout(device_io.display, (BasicTextView(device_io.display), Style()))
        self.view[0][0].update(0, 'Score: 0')
        _, hud_height = self.view[0][0].get_width_height()
        self.view.append((InvadersScreen(device_io.display, self, self.device_io.display.width, self.device_io.display.height - hud_height), Style(posType=0b01)))

        width, height = self.view[1][0].get_width_height()
        self.pos_x = width / 2
        self.pos_y = height / 2
        self.move_x = 0
        self.move_y = 0
        self.aim_x = 0
        self.aim_y = -1
        self.bullets = []
        self.enemies = []
        self.score = 0
        self.keep_running = True
        self.paused = False
        self.pause_sel = False

    async def run(self):
        self.device_io.accelerometer.subscribe(self.accel_event, events=['xyz'])
        self.device_io.joystick.subscribe(self.joystick_event, events=['xy', 'left-right'])
        self.device_io.buttons.subscribe(self.button_event, events=['a', 'b'])
        while self.keep_running:
            self._update()
            self._draw()
            await asyncio.sleep_ms(1)
        self.device_io.accelerometer.unsubscribe(self.accel_event, events=['xyz'])
        self.device_io.joystick.unsubscribe(self.joystick_event, events=['xy', 'left-right'])
        self.device_io.buttons.unsubscribe(self.button_event, events=['a', 'b'])

    def accel_event(self, event, xyz):
        self.move_x = xyz['x'] * self.speed * -1
        self.move_y = xyz['y'] * self.speed * -1

    def joystick_event(self, event, xy):
        if self.paused:
            if event == 'left-right':
                self.pause_sel = not self.pause_sel
                if self.pause_sel:
                    self.view[0][0].update(0, 'Exit?   >yes    no')
                else:
                    self.view[0][0].update(0, 'Exit?    yes   >no')
            return
        if event == 'xy' and (xy['x'] != 0 or xy['y'] != 0):
            x = 0.5 - xy['x']
            y = xy['y'] - 0.5
            norm = math.sqrt(x * x + y * y)
            if norm > 0.1:
                self.aim_x = x / norm
                self.aim_y = y / norm

    def button_event(self, button, pressed):
        if not pressed:
            return
        if self.paused:
            if button == 'a':
                if self.pause_sel:
                    self.keep_running = False
                    self.paused = False
                else:
                    self.paused = False
            elif button == 'b':
                self.paused = False
            return
        if button == 'a':
            self.bullets.append((self.pos_x, self.pos_y, self.aim_x, self.aim_y))
        elif button == 'b':
            self.paused = True
            self.pause_sel = True
            self.view[0][0].update(0, 'Exit?   >yes    no ')

    def _update(self):
        if self.paused:
            return
        width, height = self.view[1][0].get_width_height()

        # ship
        self.pos_x = min(width - 1, max(0, self.pos_x + self.move_x))
        self.pos_y = min(height - 1, max(0, self.pos_y + self.move_y))

        # bullets
        i = 0
        while i < len(self.bullets):
            x, y, dx, dy = self.bullets[i]
            x += dx * self.bullet_speed
            y += dy * self.bullet_speed
            if x < 0 or x >= width or y < 0 or y >= width:
                self.bullets.pop(i)
                continue
            self.bullets[i] = (x, y, dx, dy)
            i += 1

    def _draw(self):
        if not self.paused:
            self.view[0][0].update(0, f'Score: {self.score}')
        self.view.render()
