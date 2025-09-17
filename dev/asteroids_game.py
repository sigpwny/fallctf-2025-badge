from array import array
import asyncio
import time
import random
import math

from menu import Runnable
from ST7735 import TFT

from logger import log


class Asteroid:
    # __slots__ = (...)
    def __init__(self, x: int, y: int, size: int):
        self.x = x
        self.y = y
        self.size = size
        self.hitbox_radius = size

    def draw(self, display, view_transform):
        x, y = view_transform(self.x, self.y)
        if x < -self.size or x > 160 + self.size or y < -self.size or y > 128 + self.size:
            return
        display.fill_circle(x, y, self.size, TFT.GRAY)
        display.draw_circle(x, y, self.size, TFT.WHITE)



class Missile:
    # __slots__ = (...)
    def __init__(self, x: int, y: int, dir_: float, init_speed: float, acceleration: float, top_speed: float, lifetime: int):
        self.x = x
        self.y = y
        self.dir_ = dir_ # in radians
        self.speed = init_speed # in pixels per ms
        self.acceleration = acceleration
        self.top_speed = top_speed
        self.lifetime = lifetime # in ms
        self.hitbox_radius = 4
        self.draw_radius = 2
        self.exploded = None # set to a timestamp once exploded
        self.ended = False

    def update(self, dt):
        if self.exploded is None:
            # keep accelerating until top speed
            if self.speed < self.top_speed:
                self.speed += self.acceleration * dt
                if self.speed > self.top_speed:
                    self.speed = self.top_speed
            self.x += self.speed * math.cos(self.dir_) * dt
            self.y += self.speed * math.sin(self.dir_) * dt

            self.lifetime -= dt
            if self.lifetime <= 0:
                self.exploded = time.ticks_ms()

    def draw(self, display, view_transform):
        if self.ended:
            return
        if self.exploded is not None:
            # draw explosion
            elapsed = time.ticks_diff(time.ticks_ms(), self.exploded)
            if elapsed > 500:
                self.ended = True
                return
            radius = int(elapsed / 500 * 6)
            x, y = view_transform(self.x, self.y)
            display.fill_circle(x, y, radius, TFT.YELLOW)
            display.draw_circle(x, y, radius, TFT.RED)
        else:
            x, y = view_transform(self.x, self.y)
            display.fill_circle(x, y, self.draw_radius, TFT.RED)

    def check_collision(self, asteroids_and_other_missiles):
        for obj in asteroids_and_other_missiles:
            if obj is self or self.exploded is not None:
                continue
            dist_sq = (obj.x - self.x) ** 2 + (obj.y - self.y) ** 2
            min_dist = self.hitbox_radius + obj.hitbox_radius
            if dist_sq < min_dist ** 2:
                log('Missile hit something!')
                self.exploded = time.ticks_ms()
                return

    def check_collision_with_ship(self, ship):
        dist_sq = (ship.x - self.x) ** 2 + (ship.y - self.y) ** 2
        min_dist = self.hitbox_radius + ship.hitbox_radius
        if dist_sq < min_dist ** 2:
            self.exploded = time.ticks_ms()
            ship.health -= 40
            log(f'Ship hit by missile! Health: {ship.health}')
            if ship.health < 0:
                ship.health = 0

class Ship:
    MAX_SPEED = 2e-2
    
    def __init__(self):
        self.x = 80
        self.y = 100
        self.old_x = self.x
        self.old_y = self.y
        self.screen_x = 80
        self.screen_y = 100
        self.vel = 0
        self.vdir = -math.pi/2  # in radians
        self.angular_velocity = 0  # in radians per ms
        self.health = 100
        self.hitbox_radius = 6
        self.stardust = 0

    def draw(self, display):
        x, y = self.screen_x, self.screen_y
        display.draw_circle(x, y, self.hitbox_radius, TFT.WHITE)
        arr = array('h', [0, -6, -3, 3, 3, 3])
        display.poly(x, y, arr, TFT.PURPLE, True)

    def apply_view_around_ship(self, x: int, y: int):
        x_shifted = x - self.x
        y_shifted = y - self.y
        x_rot = self.cos_a * x_shifted - self.sin_a * y_shifted
        y_rot = self.sin_a * x_shifted + self.cos_a * y_shifted
        return int(x_rot + self.screen_x), int(y_rot + self.screen_y)

    def update(self, vel_change, rot_change, dt):
        # dt units of milliseconds

        self.angular_velocity += rot_change
        self.vdir += self.angular_velocity * dt
        self.vdir %= 2 * math.pi
        self.angular_velocity *= 0.9  # damping
        self.vel += vel_change
        self.vel *= 0.99  # damping
        if self.vel > self.MAX_SPEED:
            self.vel = self.MAX_SPEED
        elif self.vel < -self.MAX_SPEED:
            self.vel = -self.MAX_SPEED

        self.cos_a = math.cos(-self.vdir - math.pi/2)
        self.sin_a = math.sin(-self.vdir - math.pi/2)

        dx = self.vel * math.cos(self.vdir) * dt
        dy = self.vel * math.sin(self.vdir) * dt

        self.old_x = self.x
        self.old_y = self.y
        self.x += dx
        self.y += dy

    def check_asteroid_collision(self, asteroids):
        for asteroid in asteroids:
            dist_sq = (asteroid.x - self.x) ** 2 + (asteroid.y - self.y) ** 2
            min_dist = self.hitbox_radius + asteroid.size
            if dist_sq < min_dist ** 2:
                self.health -= 10
                if self.health < 0:
                    self.health = 0
                log(f'Collision! Health: {self.health}')
                # Simple collision response: go back to old position
                self.x = self.old_x
                self.y = self.old_y
                # Bounce off the asteroid
                self.vel = -self.vel * 0.5

    def gain_star(self):
        self.stardust += 1
        log(f'Gained a star! Total stardust: {self.stardust}')


class Star:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.hitbox_radius = 2

    def draw(self, display, view_transform):
        x, y = view_transform(self.x, self.y)
        if x < -self.hitbox_radius or x > 160 + self.hitbox_radius or y < -self.hitbox_radius or y > 128 + self.hitbox_radius:
            return
        display.fill_circle(x, y, self.hitbox_radius, TFT.YELLOW)


class GameWorld:
    def __init__(self):
        self.asteroids = []
        self.missiles = []
        self.my_ship = Ship()
        self.stars = []
        self.last_missile_launch = 0

    def generate(self, num_asteroids=30, num_stars=10):
        for _ in range(num_asteroids):
            x = random.randint(0, 160)
            y = random.randint(0, 256)
            size = random.randint(5, 15)
            # avoid spawning too close to the ship
            if (x - self.my_ship.x) ** 2 + (y - self.my_ship.y) ** 2 < 30 ** 2:
                continue
            self.asteroids.append(Asteroid(x, y, size))

        for _ in range(num_stars):
            x = random.randint(0, 160)
            y = random.randint(0, 256)
            # avoid spawning too close to the ship
            if (x - self.my_ship.x) ** 2 + (y - self.my_ship.y) ** 2 < 20 ** 2:
                continue
            self.stars.append(Star(x, y))

    def draw_nearest_star_indicator(self, display):
        # first, find the nearest star
        if not self.stars:
            return
        nearest_star = min(self.stars, key=lambda star: (star.x - self.my_ship.x) ** 2 + (star.y - self.my_ship.y) ** 2)

    def update(self, vel_change, rot_change, dt):
        self.my_ship.update(vel_change, rot_change, dt)
        self.my_ship.check_asteroid_collision(self.asteroids)

        in_flight_missiles = [m for m in self.missiles if m.exploded is None and not m.ended]
        for missile in in_flight_missiles:
            missile.update(dt)
            missile.check_collision(self.asteroids + in_flight_missiles)
            missile.check_collision_with_ship(self.my_ship)
        # Remove ended missiles
        self.missiles = [m for m in self.missiles if not m.ended]

        new_stars = []
        for star in self.stars:
            if (star.x - self.my_ship.x) ** 2 + (star.y - self.my_ship.y) ** 2 < (star.hitbox_radius + self.my_ship.hitbox_radius) ** 2:
                self.stars.append(Star(random.randint(0, 160), random.randint(0, 256)))
                self.my_ship.gain_star()
            else:
                new_stars.append(star)
        self.stars = new_stars

    def draw(self, display):
        # background
        display.display.fill(TFT.color(10, 7, 89))

        # asteroids
        # NOTE: drawing these one by one is slow, consider batching
        for asteroid in self.asteroids:
            asteroid.draw(display.display, self.my_ship.apply_view_around_ship)

        # health bar
        display.display.fill_rect(20, 120, 120, 5, TFT.WHITE)
        display.display.fill_rect(20, 120, int(self.my_ship.health * 1.2), 5, TFT.RED)

        # missiles
        for missile in self.missiles:
            missile.draw(display.display, self.my_ship.apply_view_around_ship)

        # stars
        for star in self.stars:
            star.draw(display.display, self.my_ship.apply_view_around_ship)

        # ship
        self.my_ship.draw(display.display)

    def fire_missile(self):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_missile_launch) < 500:
            return
        self.last_missile_launch = current_time
        
        log('Firing missile!')
        self.missiles.append(
            Missile(
                x=self.my_ship.x + math.cos(self.my_ship.vdir) * 10,
                y=self.my_ship.y + math.sin(self.my_ship.vdir) * 10,
                dir_=self.my_ship.vdir,
                init_speed=0.001 + self.my_ship.vel,
                acceleration=0.0001,
                top_speed=0.1,
                lifetime=1500
            )
        )
        


class AsteroidsGame(Runnable):
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io
        self.world = GameWorld()
        self.joystick_x = 0
        self.joystick_y = 0
        self.last_update_time = time.ticks_ms()

    def _update(self):
        current_time = time.ticks_ms()
        dt = time.ticks_diff(current_time, self.last_update_time)
        # log(f'dt={dt} ms, joystick_x={self.joystick_x}, joystick_y={self.joystick_y}')
        self.world.update(
            vel_change=self.joystick_y * 1e-3,
            rot_change=self.joystick_x * 1e-4,
            dt=dt
        )
        self.last_update_time = current_time

    def _draw(self, fps=None):
        self.world.draw(self.device_io.display)
        if fps is not None:
            self.device_io.display.draw_text(0, 0, f'FPS: {fps:.1f}')
        self.device_io.display.show()

    def _joystick_event(self, event, val):
        if event != 'xy':
            return
        joystick_x = val['x']
        joystick_y = val['y']
        self.joystick_x = -(joystick_x - 0.5) * 2
        self.joystick_y = -(joystick_y - 0.5) * 2

    def _button_event(self, button, pressed):
        if not pressed:
            return
        if button == 'a':
            self.world.fire_missile()

    async def run(self):
        self.device_io.joystick.subscribe(self._joystick_event, events=['xy'])
        self.device_io.buttons.subscribe(self._button_event, events=['a'])
        
        self.world.generate()
        start_time = time.ticks_ms()
        num_frames = 0
        while True:
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            num_frames += 1
            fps = num_frames * 1000 / elapsed if elapsed > 0 else 0

            self._update()
            self._draw(fps)

            await asyncio.sleep_ms(1)

        self.device_io.joystick.unsubscribe(self._joystick_event, events=['xy'])
        self.device_io.buttons.unsubscribe(self._button_event, events=['a'])
