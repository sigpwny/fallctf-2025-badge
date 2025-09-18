from array import array
import asyncio
import time
import random
import math

from menu import Runnable, menu_with_text
from ST7735 import TFT

from logger import log


JOYSTICK_VEL_SCALE = 1e-3
JOYSTICK_ROT_SCALE = 1e-4


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
    def __init__(self, x: int, y: int, dir_: float, init_speed: float, acceleration=0.0001, top_speed=0.1, lifetime=1500):
        self.x = x
        self.y = y
        self.dir_ = dir_ # in radians
        self.speed = init_speed # in pixels per ms
        self.exploded = None # set to a timestamp once exploded
        self.id_ = random.getrandbits(16)

        self.ended = False
        self.acceleration = acceleration
        self.top_speed = top_speed
        self.lifetime = lifetime # in ms
        self.hitbox_radius = 4
        self.draw_radius = 2

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

    def __init__(self, x=80, y=100, vdir=-math.pi/2):
        self.x = x
        self.y = y
        self.vel = 0
        self.vdir = vdir  # in radians

        self.old_x = self.x
        self.old_y = self.y
        self.screen_x = 80
        self.screen_y = 100
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

class Star:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.hitbox_radius = 2
        self.id_ = random.getrandbits(16)

    def draw(self, display, view_transform):
        x, y = view_transform(self.x, self.y)
        if x < -self.hitbox_radius or x > 160 + self.hitbox_radius or y < -self.hitbox_radius or y > 128 + self.hitbox_radius:
            return
        display.fill_circle(x, y, self.hitbox_radius, TFT.YELLOW)


class BroadcastUpdate:
    ASTEROID = 0
    SHIP_AND_MISSILE = 1
    INIT_STAR = 3
    REMOVE_STAR = 4


class ClientUpdate:
    MOVE = 0
    FIRE_MISSILE = 1


class GameServer:
    def __init__(self, send_raw_msg_func=None):
        self.asteroids = []
        self.missiles = []
        self.ships = []
        self.stars = []
        self.last_update_time = time.ticks_ms()
        self.send_raw_msg_func = send_raw_msg_func
        self.running = True

        self.ships.append(Ship(x=32080, y=32100, vdir=-math.pi/2))
        self.ships.append(Ship(x=32040, y=32050, vdir=math.pi/2))

    def generate(self, num_asteroids=30, num_stars=10):
        for _ in range(num_asteroids):
            x = random.randint(32000, 32200)
            y = random.randint(32000, 32200)
            size = random.randint(5, 15)
            # avoid spawning too close to the ship
            for ship in self.ships:
                if (x - ship.x) ** 2 + (y - ship.y) ** 2 < (20 + size) ** 2:
                    break
            else:
                self.asteroids.append(Asteroid(x, y, size))

        for _ in range(num_stars):
            x = random.randint(32000, 32200)
            y = random.randint(32000, 32200)
            # avoid spawning too close to the ship
            for ship in self.ships:
                if (x - ship.x) ** 2 + (y - ship.y) ** 2 < (20) ** 2:
                    continue
            self.stars.append(Star(x, y))

    def update(self, ship_id, vel_change, rot_change, dt):
        self.ships[ship_id].update(vel_change, rot_change, dt)
        self.ships[ship_id].check_asteroid_collision(self.asteroids)

        in_flight_missiles = [m for m in self.missiles if m.exploded is None and not m.ended]
        for missile in in_flight_missiles:
            missile.update(dt)
            missile.check_collision(self.asteroids + in_flight_missiles)
            for ship in self.ships:
                missile.check_collision_with_ship(ship)
        # Remove ended missiles
        self.missiles = [m for m in self.missiles if not m.ended]

        new_stars = []
        for star in self.stars:
            for ship in self.ships:
                dist_sq = (star.x - ship.x) ** 2 + (star.y - ship.y) ** 2
                min_dist = star.hitbox_radius + ship.hitbox_radius
                if dist_sq < min_dist ** 2:
                    self.broadcast_remove_star(star.id_, ship_id)
                    break
            else:
                new_stars.append(star)
        self.stars = new_stars

    def fire_missile(self, ship_index=0):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_missile_launch) < 500:
            return
        self.last_missile_launch = current_time

        log('Firing missile!')
        ship = self.ships[ship_index]
        self.missiles.append(
            Missile(
                x=ship.x + math.cos(ship.vdir) * 15,
                y=ship.y + math.sin(ship.vdir) * 15,
                dir_=ship.vdir,
                init_speed=0.001 + ship.vel,
            )
        )

    def broadcast_remove_star(self, star_id, gained_ship_id):
        msg = bytearray([BroadcastUpdate.REMOVE_STAR])
        msg += int(star_id).to_bytes(2, 'little')
        msg += int(gained_ship_id).to_bytes(1, 'little')
        self.send_raw_msg(msg)
        log(f'Ship {gained_ship_id} collected a star!')

    def broadcast_update(self, update_type):
        if update_type == BroadcastUpdate.ASTEROID:
            msg = bytearray([BroadcastUpdate.ASTEROID])
            for asteroid in self.asteroids:
                msg += int(asteroid.x).to_bytes(2, 'little')
                msg += int(asteroid.y).to_bytes(2, 'little')
                msg += int(asteroid.size).to_bytes(1, 'little')
                if len(msg) > 240:
                    log('Too many asteroids to send in one message!', level='prod')
                    break
            self.send_raw_msg(msg)
        elif update_type == BroadcastUpdate.SHIP_AND_MISSILE:
            msg = bytearray([BroadcastUpdate.SHIP_AND_MISSILE])
            for ship in self.ships:
                msg += int(ship.x).to_bytes(2, 'little')
                msg += int(ship.y).to_bytes(2, 'little')
                vel_scaled = ship.vel * 20
                if vel_scaled < -1:
                    vel_scaled = -1
                elif vel_scaled > 1:
                    vel_scaled = 1
                msg += int(vel_scaled * (1<<15) + (1<<15)).to_bytes(2, 'little')
                msg += int(ship.vdir /(2 * math.pi) * 65535).to_bytes(2, 'little')
                msg += int(ship.health).to_bytes(1, 'little')
            for missile in self.missiles:
                # no need to draw animations, so we'll mark a missile as ended once we notify others
                if missile.ended:
                    continue
                if missile.exploded is not None:
                    missile.ended = True # mark as ended for next update
                msg += int(missile.x).to_bytes(2, 'little')
                msg += int(missile.y).to_bytes(2, 'little')
                msg += int(missile.dir_ /(2 * math.pi) * 65535).to_bytes(2, 'little')
                msg += int(missile.speed * 1e5).to_bytes(2, 'little')
                msg += int(0 if missile.exploded is None else 1).to_bytes(1, 'little')
                msg += int(missile.id_).to_bytes(2, 'little')
                if len(msg) > 240:
                    log('Too many missiles to send in one message!', level='prod')
                    break
            self.send_raw_msg(msg)
        elif update_type == BroadcastUpdate.INIT_STAR:
            msg = bytearray([BroadcastUpdate.INIT_STAR])
            for star in self.stars:
                msg += int(star.x).to_bytes(2, 'little')
                msg += int(star.y).to_bytes(2, 'little')
                msg += int(star.id_).to_bytes(2, 'little')
                if len(msg) > 240:
                    log('Too many stars to send in one message!', level='prod')
                    break
            self.send_raw_msg(msg)
        elif update_type == BroadcastUpdate.REMOVE_STAR:
            # this should be handled immediately when a star is collected
            pass

    def send_raw_msg(self, msg):
        if self.send_raw_msg_func is not None:
            # log(f'[SERVER] sending raw msg: {msg.hex()}')
            self.send_raw_msg_func(msg)

    def raw_msg_from_client(self, raw_data):
        # log(f'[SERVER] received raw msg from client {client_id}: {raw_data.hex()}')
        try:
            client_id = raw_data[0]
            msg_type = raw_data[1]
            if msg_type == ClientUpdate.MOVE:
                joy_x = int.from_bytes(raw_data[2:4], 'little') / 32767 - 1
                joy_y = int.from_bytes(raw_data[4:6], 'little') / 32767 - 1
                self.update_from_client(client_id, joy_x, joy_y)
            elif msg_type == ClientUpdate.FIRE_MISSILE:
                self.fire_missile(ship_index=client_id)
        except IndexError:
            log(f'Malformed message from client: {raw_data.hex()}', level='prod')


    def update_from_client(self, client_id, joy_x, joy_y):
        current_time = time.ticks_ms()
        dt = time.ticks_diff(current_time, self.last_update_time)
        vel_change = joy_y * JOYSTICK_VEL_SCALE
        rot_change = joy_x * JOYSTICK_ROT_SCALE
        self.update(client_id, vel_change, rot_change, dt)
        self.last_update_time = current_time

    async def run(self):
        self.generate()

        await asyncio.sleep_ms(100)
        self.broadcast_update(BroadcastUpdate.ASTEROID)
        await asyncio.sleep_ms(100)
        self.broadcast_update(BroadcastUpdate.INIT_STAR)
        self.last_missile_launch = time.ticks_ms()

        while self.running:
            self.broadcast_update(BroadcastUpdate.SHIP_AND_MISSILE)
            await asyncio.sleep_ms(50)


class GameClient:
    def __init__(self, client_id):
        self.asteroids = []
        self.missiles = []
        self.my_ship = Ship()
        self.stars = []
        self.last_missile_launch = 0
        self.client_id = client_id
        self.raw_msg_server_func = None
        self.last_send_move_update = time.ticks_ms()

    def update(self, joystick_x, joystick_y, dt):
        vel_change = joystick_y * JOYSTICK_VEL_SCALE
        rot_change = joystick_x * JOYSTICK_ROT_SCALE
        self.my_ship.update(vel_change, rot_change, dt)

        for missile in self.missiles:
            if missile.exploded is None:
                missile.update(dt)

        # remove ended missiles
        self.missiles = [m for m in self.missiles if not m.ended]

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_send_move_update) > 50:
            msg = bytearray([self.client_id, ClientUpdate.MOVE])
            msg += int((joystick_x + 1) * 32767).to_bytes(2, 'little')
            msg += int((joystick_y + 1) * 32767).to_bytes(2, 'little')
            self.raw_msg_server_func(msg)
            self.last_send_move_update = now

    def update_from_server(self, raw_data):
        msg_type = raw_data[0]
        if msg_type == BroadcastUpdate.ASTEROID:
            self.asteroids = []
            idx = 1
            while idx + 4 <= len(raw_data):
                x = int.from_bytes(raw_data[idx:idx+2], 'little')
                y = int.from_bytes(raw_data[idx+2:idx+4], 'little')
                size = raw_data[idx+4]
                self.asteroids.append(Asteroid(x, y, size))
                idx += 5
        elif msg_type == BroadcastUpdate.INIT_STAR:
            self.stars = []
            idx = 1
            while idx + 5 <= len(raw_data):
                x = int.from_bytes(raw_data[idx:idx+2], 'little')
                y = int.from_bytes(raw_data[idx+2:idx+4], 'little')
                star_id = int.from_bytes(raw_data[idx+4:idx+6], 'little')
                self.stars.append(Star(x, y))
                self.stars[-1].id_ = star_id
                idx += 6
        elif msg_type == BroadcastUpdate.REMOVE_STAR:
            star_id = int.from_bytes(raw_data[1:3], 'little')
            gained_ship_id = raw_data[3]
            self.stars = [s for s in self.stars if s.id_ != star_id]
            if gained_ship_id == self.client_id:
                self.my_ship.stardust += 1
                log(f'Collected a star! Total stardust: {self.my_ship.stardust}')
        elif msg_type == BroadcastUpdate.SHIP_AND_MISSILE:
            num_ships = 2
            idx = 1
            for i in range(num_ships):
                x = int.from_bytes(raw_data[idx:idx+2], 'little')
                y = int.from_bytes(raw_data[idx+2:idx+4], 'little')
                vel_raw = int.from_bytes(raw_data[idx+4:idx+6], 'little')
                vel = (vel_raw - (1<<15)) / (1<<15) / 20
                vdir = int.from_bytes(raw_data[idx+6:idx+8], 'little') / 65535 * 2 * math.pi
                health = raw_data[idx+8]
                if i == self.client_id:
                    self.my_ship.x = x
                    self.my_ship.y = y
                    self.my_ship.vel = vel
                    self.my_ship.vdir = vdir
                    self.my_ship.cos_a = math.cos(-vdir - math.pi/2)
                    self.my_ship.sin_a = math.sin(-vdir - math.pi/2)
                    self.my_ship.health = health
                idx += 9
            while idx + 9 <= len(raw_data):
                x = int.from_bytes(raw_data[idx:idx+2], 'little')
                y = int.from_bytes(raw_data[idx+2:idx+4], 'little')
                dir_ = int.from_bytes(raw_data[idx+4:idx+6], 'little') / 65535 * 2 * math.pi
                speed = int.from_bytes(raw_data[idx+6:idx+8], 'little') / 1e5
                exploded = raw_data[idx+8]
                missile_id = int.from_bytes(raw_data[idx+9:idx+11], 'little')
                # either create new missile or update existing one
                for missile in self.missiles:
                    if missile.id_ == missile_id:
                        missile.x = x
                        missile.y = y
                        missile.dir_ = dir_
                        missile.speed = speed
                        if exploded and missile.exploded is None:
                            missile.exploded = time.ticks_ms()
                        break
                else:
                    missile = Missile(x, y, dir_, speed)
                    missile.id_ = missile_id
                    if exploded and missile.exploded is None:
                        missile.exploded = time.ticks_ms()
                    self.missiles.append(missile)
                idx += 11


    def fire_missile(self):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_missile_launch) < 500:
            return
        self.last_missile_launch = current_time

        msg = bytearray([self.client_id, ClientUpdate.FIRE_MISSILE])
        self.raw_msg_server_func(msg)

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
        # NOTE: drawing these one by one is slow, consider batching
        for star in self.stars:
            star.draw(display.display, self.my_ship.apply_view_around_ship)

        # ship
        self.my_ship.draw(display.display)


class AsteroidsGameClient(Runnable):
    def __init__(self, device_io: "DeviceIO", wifi_client_id, wifi_client_send_fn):
        self.device_io = device_io
        self.world = GameClient(wifi_client_id)
        self.world.raw_msg_server_func = wifi_client_send_fn
        self.joystick_x = 0
        self.joystick_y = 0
        self.last_update_time = time.ticks_ms()
        self.paused = False

    def wifi_recv_callback(self, msg):
        """
        Receive message from wifi and pass to client
        """
        self.world.update_from_server(msg)

    def _update(self):
        current_time = time.ticks_ms()
        dt = time.ticks_diff(current_time, self.last_update_time)
        self.world.update(self.joystick_x, self.joystick_y, dt)
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
        if button == 'a' and not self.paused:
            self.world.fire_missile()
        elif button == 'b':
            self.paused = True

    async def run(self):
        self.device_io.joystick.subscribe(self._joystick_event, events=['xy'])
        self.device_io.buttons.subscribe(self._button_event, events=['a', 'b'])

        start_time = time.ticks_ms()
        num_frames = 0
        while True:
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            num_frames += 1
            fps = num_frames * 1000 / elapsed if elapsed > 0 else 0

            self._update()
            self._draw(fps)

            await asyncio.sleep_ms(1)

            if self.paused:
                await menu_with_text(
                    self.device_io,
                    ['Game Paused'],
                    [
                        ('Resume', None, lambda: setattr(self, 'paused', False)),
                        ('End game', None, lambda: None)
                    ]
                )

        self.device_io.joystick.unsubscribe(self._joystick_event, events=['xy'])
        self.device_io.buttons.unsubscribe(self._button_event, events=['a', 'b'])


class AsteroidsGameServerAndClient(Runnable):
    def __init__(self, device_io: "DeviceIO", wifi_client_id, wifi_server_send_fn):
        self.server = GameServer(send_raw_msg_func=self._server_send_fn)
        self.client = AsteroidsGameClient(device_io, wifi_client_id, self._client_send_fn)
        self.wifi_server_send_fn = wifi_server_send_fn

    def _server_send_fn(self, msg):
        """
        Broadcast message to both the local client and over the wifi
        """
        self.client.wifi_recv_callback(msg)
        self.wifi_server_send_fn(msg)

    def _client_send_fn(self, msg):
        """
        Send message from the local client to the server
        """
        self.server.raw_msg_from_client(msg)

    def wifi_recv_callback(self, msg):
        """
        Receive message from wifi and pass to server
        """
        self.server.raw_msg_from_client(msg)

    async def run(self):
        server_task = asyncio.create_task(self.server.run())
        client_task = asyncio.create_task(self.client.run())
        await asyncio.gather(server_task, client_task)
