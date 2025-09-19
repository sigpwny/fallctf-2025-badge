import asyncio
import math
from array import array
import random

from display import Display
from menu import Runnable
from view import BasicTextView, View
from layout import ComplexLayout, Style
from ST7735 import TFT

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


FOLLOWER_ENEMY = 1
PREDICTOR_ENEMY = 2
MOMENTUM_ENEMY = 3

BACKGROUND = TFT.color(10, 7, 89)
LIGHT_RED = TFT.color(0xFF, 0x33, 0x33)

PLAYER_SPEED = 5
BULLET_SPEED = 10
ENEMY_SPEED = 0.5

MAX_ENEMIES = 10
MAX_BULLETS = 10


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
        self.display.display.fill_rect(x, y + 1, x2, y2, BACKGROUND)

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
        for pos_x, pos_y, _, _, type in self.game.enemies:
            c = self.display.display.tft.GREEN if type == FOLLOWER_ENEMY else (self.display.display.tft.PURPLE if type == PREDICTOR_ENEMY else LIGHT_RED)
            self.display.display.ellipse(int(pos_x) + x, int(pos_y) + y + 1, 5, 2, c, True)
            self.display.display.ellipse(int(pos_x) + x, int(pos_y) + y - 1, 3, 2, c, True)
            self.display.display.ellipse(int(pos_x) + x, int(pos_y) + y - 1, 2, 1, self.display.display.tft.BLACK, True)

    def get_width_height(self) -> tuple[int, int]:
        return (self.width, self.height)


class InvadersGame(Runnable):
    def __init__(self, device_io: 'DeviceIO') -> None:
        self.device_io = device_io

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
        self.bullets: list[tuple[float, float, float, float]] = []
        self.enemies: list[tuple[float, float, float, float, int]] = []
        self.score = 0
        self.keep_running = True
        self.paused = False
        self.pause_sel = False
        self.game_over = False

    async def run(self):
        self.device_io.accelerometer.subscribe(self.accel_event, events=['xyz'])
        self.device_io.joystick.subscribe(self.joystick_event, events=['xy', 'left-right'])
        self.device_io.buttons.subscribe(self.button_event, events=['a', 'b'])
        asyncio.create_task(self.spawn_enemies())
        while self.keep_running:
            self._update()
            self._draw()
            await asyncio.sleep_ms(1)
        if self.game_over:
            self.view[0][0].update(0, 'Game Over!')
            self.view.render()
            await asyncio.sleep(3)
            self.view[0][0].update(0, f'Score: {self.score}')
            self.view.render()
            await asyncio.sleep(3)
        self.device_io.accelerometer.unsubscribe(self.accel_event, events=['xyz'])
        self.device_io.joystick.unsubscribe(self.joystick_event, events=['xy', 'left-right'])
        self.device_io.buttons.unsubscribe(self.button_event, events=['a', 'b'])

    async def spawn_enemies(self):
        width, _ = self.view[1][0].get_width_height()
        _, hud_height = self.view[0][0].get_width_height()
        while self.keep_running:
            if self.paused:
                await asyncio.sleep(0.1)
                continue
            if len(self.enemies) >= MAX_ENEMIES:
                await asyncio.sleep(0.1)
                continue
            # the higher the score, the more likely to spawn harder enemies
            if random.randint(0, self.score // 10) == 0:
                self.enemies.append((random.random() * width, hud_height, 0, 0, FOLLOWER_ENEMY))
            elif random.randint(0, self.score // 20) == 0:
                self.enemies.append((random.random() * width, hud_height, 0, 0, PREDICTOR_ENEMY))
            else:
                self.enemies.append((random.random() * width, hud_height, 0, 0, MOMENTUM_ENEMY))
            await asyncio.sleep(1)

    def accel_event(self, event, xyz):
        self.move_x = xyz['x'] * PLAYER_SPEED * -1
        self.move_y = xyz['y'] * PLAYER_SPEED * -1

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
            if len(self.bullets) < MAX_BULLETS:
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
            x += dx * BULLET_SPEED
            y += dy * BULLET_SPEED
            if x < 0 or x >= width or y < 0 or y >= width:
                self.bullets.pop(i)
                continue
            self.bullets[i] = (x, y, dx, dy)
            i += 1

        # enemies
        i = 0
        while i < len(self.enemies):
            x, y, dx, dy, t = self.enemies[i]
            dead = False
            for j in range(len(self.bullets)):
                bx, by, _, _ = self.bullets[j]
                dbx = x - bx
                dby = y - by
                norm_sqr = dbx * dbx + dby * dby
                if norm_sqr < 36:
                    self.enemies.pop(i)
                    self.bullets.pop(j)
                    dead = True
                    self.score += 1 if t == FOLLOWER_ENEMY else (2 if t == PREDICTOR_ENEMY else 5)
                    break
            if dead:
                continue
            dpx = self.pos_x - x
            dpy = self.pos_y - y
            norm = math.sqrt(dpx * dpx + dpy * dpy)
            if norm < 7:
                self.game_over = True
                self.keep_running = False
            if t == FOLLOWER_ENEMY:
                x += dpx / norm * ENEMY_SPEED
                y += dpy / norm * ENEMY_SPEED
            elif t == PREDICTOR_ENEMY:
                dpx += self.move_x * 20
                dpy += self.move_y * 20
                norm = math.sqrt(dpx * dpx + dpy * dpy)
                x += dpx / norm * ENEMY_SPEED
                y += dpy / norm * ENEMY_SPEED
            elif t == MOMENTUM_ENEMY:
                dx += dpx / norm
                dy += dpy / norm
                dx *= 0.999
                dy *= 0.999
                x += dx * ENEMY_SPEED * 0.1
                y += dy * ENEMY_SPEED * 0.1
            else:
                self.enemies.pop(i)
                continue
            self.enemies[i] = (x, y, dx, dy, t)
            i += 1

    def _draw(self):
        if not self.paused:
            self.view[0][0].update(0, f'Score: {self.score}')
        self.view.render()
