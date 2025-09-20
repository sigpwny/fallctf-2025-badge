from array import array
import asyncio
import time
import random
import math
import struct

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
        self.damage = size * 2

    def draw(self, display, view_transform):
        x, y = view_transform(self.x, self.y)
        if x < -self.size or x > 160 + self.size or y < -self.size or y > 128 + self.size:
            return
        display.fill_circle(x, y, self.size, TFT.GRAY)
        display.draw_circle(x, y, self.size, TFT.WHITE)



class Missile:
    # __slots__ = (...)
    def __init__(self, x: int, y: int, dir_: float, init_speed: float, damage: int, acceleration=1e-4, top_speed=5e-2, lifetime=2000):
        self.x = x
        self.y = y
        self.dir_ = dir_ # in radians
        self.speed = init_speed # in pixels per ms
        self.exploded = None # set to a timestamp once exploded
        self.id_ = random.getrandbits(16)
        self.damage = damage

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
            ship.damage += self.damage
            log(f'Ship hit by missile! Health: {ship.max_health - ship.damage}')

class Ship:
    MAX_SPEED = 2e-2

    def __init__(self, x=80, y=100, init_health=100, vdir=-math.pi/2):
        self.x = x * 1.0
        self.y = y * 1.0
        self.vel = 0.0
        self.vdir = vdir * 1.0  # in radians
        self.angular_velocity = 0.0  # in radians per ms

        self.sin_a = math.sin(-vdir - math.pi/2)
        self.cos_a = math.cos(-vdir - math.pi/2)
        self.old_x = self.x
        self.old_y = self.y
        self.screen_x = 80
        self.screen_y = 100
        self.damage = 0
        self.max_health = init_health
        self.hitbox_radius = 6
        self.stardust = 0

    def draw_other(self, display, view_transform):
        # x, y = view_transform(self.x, self.y)
        # display.draw_circle(x, y, self.hitbox_radius, TFT.WHITE)

        ship_tip = self.x + math.cos(self.vdir) * 6, self.y + math.sin(self.vdir) * 6
        ship_left = self.x + math.cos(self.vdir + 2.5) * 6, self.y + math.sin(self.vdir + 2.5) * 6
        ship_right = self.x + math.cos(self.vdir - 2.5) * 6, self.y + math.sin(self.vdir - 2.5) * 6
        coords = array('h', view_transform(*ship_tip) + view_transform(*ship_left) + view_transform(*ship_right))
        display.poly(0, 0, coords, TFT.PURPLE, True)

    def draw(self, display):
        x, y = self.screen_x, self.screen_y
        # display.draw_circle(x, y, self.hitbox_radius, TFT.WHITE)
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
                self.damage += asteroid.damage
                log(f'Collision! Health: {self.max_health - self.damage}')
                # Simple collision response: go back to old position
                self.x = self.old_x
                self.y = self.old_y
                # Bounce off the asteroid
                self.vel = -self.vel * 0.5

class Star:
    STARDUST_VALUE = 25

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
    END_GAME = 5


class ClientUpdate:
    MOVE = 0
    FIRE_MISSILE = 1


class GameServer:
    SERVER_UPDATE_INTERVAL_MS = 200
    SERVER_TIMEOUT_MS = 500

    def __init__(self, send_raw_msg_func=None, freeplay=False):
        num_ships = 1 if freeplay else 2
        self.asteroids = []
        self.missiles = []
        self.ships = []
        self.stars = []
        self.last_update_time = time.ticks_ms()
        self.last_update_from_client = [0] * num_ships
        self.send_raw_msg_func = send_raw_msg_func
        self.running = True
        self.start_time = time.ticks_ms()
        self.total_duration = 60 * 1000 if not freeplay else 10 * 60 * 1000
        self.initialized = False
        self.num_ships = num_ships

        for i in range(num_ships):
            self.ships.append(Ship(x=70 + i*30, y=50, vdir=-math.pi/2))

    def generate(self, num_asteroids=30, num_stars=10):
        for _ in range(num_asteroids):
            x = random.randint(0, 200)
            y = random.randint(0, 200)
            size = random.randint(5, 15)
            # avoid spawning too close to the ship
            for ship in self.ships:
                if (x - ship.x) ** 2 + (y - ship.y) ** 2 < (20 + size) ** 2:
                    break
            else:
                self.asteroids.append(Asteroid(x, y, size))

        for _ in range(num_stars):
            x = random.randint(0, 200)
            y = random.randint(0, 200)
            # avoid spawning too close to the ship
            for ship in self.ships:
                if (x - ship.x) ** 2 + (y - ship.y) ** 2 < (20) ** 2:
                    continue
            self.stars.append(Star(x, y))

    def update(self, dt):
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
            for i, ship in enumerate(self.ships):
                dist_sq = (star.x - ship.x) ** 2 + (star.y - ship.y) ** 2
                min_dist = star.hitbox_radius + ship.hitbox_radius
                if dist_sq < min_dist ** 2:
                    self.broadcast_remove_star(star.id_, i)
                    break
            else:
                new_stars.append(star)
        self.stars = new_stars

    def fire_missile(self, ship_index, damage):
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
                init_speed=1e-3 + max(0, ship.vel),
                damage=damage
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
            remaining_time = max(0, self.total_duration - time.ticks_diff(time.ticks_ms(), self.start_time))
            msg += int(remaining_time).to_bytes(4, 'little')
            for ship in self.ships:
                msg += struct.pack(
                    '<eeeeeH',
                    ship.x,
                    ship.y,
                    ship.vel,
                    ship.vdir,
                    ship.angular_velocity,
                    ship.damage
                )
            for missile in self.missiles:
                # no need to draw animations, so we'll mark a missile as ended once we notify others
                if missile.ended:
                    continue
                if missile.exploded is not None:
                    missile.ended = True # mark as ended for next update
                msg += struct.pack(
                    '<eeeeBHB',
                    missile.x,
                    missile.y,
                    missile.dir_,
                    missile.speed,
                    0 if missile.exploded is None else 1,
                    missile.id_,
                    missile.damage
                )
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
        elif update_type == BroadcastUpdate.END_GAME:
            msg = bytearray([BroadcastUpdate.END_GAME])
            self.send_raw_msg(msg)
            self.running = False

    def send_raw_msg(self, msg):
        if self.send_raw_msg_func is not None:
            # log(f'[SERVER] sending raw msg: {msg.hex()}')
            self.send_raw_msg_func(msg)

    def raw_msg_from_client(self, raw_data):
        if raw_data == b'GAME_OVER':
            self.running = False
            self.send_raw_msg(b'GAME_OVER')
            return

        if not self.initialized:
            return

        # log(f'[SERVER] received raw msg from client {client_id}: {raw_data.hex()}')
        try:
            client_id = raw_data[0]
            msg_type = raw_data[1]
            if msg_type == ClientUpdate.MOVE:
                x, y, vel, vdir, angular_velocity, damage = struct.unpack('<eeeeeH', raw_data[2:2+12])
                ship = self.ships[client_id]
                ship.x = x
                ship.y = y
                ship.vel = vel
                ship.vdir = vdir
                ship.angular_velocity = angular_velocity
                ship.cos_a = math.cos(-vdir - math.pi/2)
                ship.sin_a = math.sin(-vdir - math.pi/2)
                ship.damage = damage
            elif msg_type == ClientUpdate.FIRE_MISSILE:
                damage = raw_data[2]
                self.fire_missile(ship_index=client_id, damage=damage)
            else:
                raise RuntimeError(f'Unknown message type {msg_type} from client')
            self.last_update_from_client[client_id] = time.ticks_ms()
            self.update_from_client()
        except IndexError:
            log(f'Malformed message from client: {raw_data.hex()}', level='prod')


    def update_from_client(self):
        current_time = time.ticks_ms()
        dt = time.ticks_diff(current_time, self.last_update_time)
        self.update(dt)
        self.last_update_time = current_time

    async def run(self):
        self.initialized = False

        self.generate()

        self.broadcast_update(BroadcastUpdate.SHIP_AND_MISSILE)
        await asyncio.sleep_ms(100)
        self.broadcast_update(BroadcastUpdate.ASTEROID)
        await asyncio.sleep_ms(100)
        self.broadcast_update(BroadcastUpdate.INIT_STAR)
        self.last_missile_launch = time.ticks_ms()
        self.last_update_time = time.ticks_ms()
        self.start_time = time.ticks_ms()

        self.initialized = True

        while self.running:
            if time.ticks_diff(time.ticks_ms(), self.start_time) > self.total_duration:
                self.running = False
                # allow it to send the last update
            self.broadcast_update(BroadcastUpdate.SHIP_AND_MISSILE)
            await asyncio.sleep_ms(self.SERVER_UPDATE_INTERVAL_MS)

            if any(
                time.ticks_diff(time.ticks_ms(), t) > self.SERVER_TIMEOUT_MS
                for t in self.last_update_from_client
            ):
                log(f'A client has not sent updates for {self.SERVER_TIMEOUT_MS} ms, ending game', level='prod')
                self.broadcast_update(BroadcastUpdate.END_GAME)


class GameClient:
    CLIENT_UPDATE_INTERVAL_MS = 200

    def __init__(self, client_id, ship_stats, freeplay):
        self.ship_stats = ship_stats
        self.asteroids = []
        self.missiles = []
        self.my_ship = Ship(init_health=100 + ship_stats.stats['shields'] * 10)
        self.my_ship_position_initialized = False
        if freeplay:
            self.other_ship = None
            self.num_ships = 1
        else:
            self.other_ship = Ship()
            self.num_ships = 2
        self.stars = []
        self.last_missile_launch = 0
        self.client_id = client_id
        self.raw_msg_server_func = None
        self.last_send_move_update = time.ticks_ms()
        self.remaining_time = 60 * 1000

    def update(self, joystick_x, joystick_y, dt):
        vel_change = joystick_y * JOYSTICK_VEL_SCALE * (1 + 0.2 * self.ship_stats.stats['thrusters'])
        rot_change = joystick_x * JOYSTICK_ROT_SCALE

        self.my_ship.update(vel_change, rot_change, dt)
        self.my_ship.check_asteroid_collision(self.asteroids)

        if self.other_ship is not None:
            self.other_ship.update(0, 0, dt)  # other ship is updated from server messages

        for missile in self.missiles:
            if missile.exploded is None:
                missile.update(dt)

        # remove ended missiles
        self.missiles = [m for m in self.missiles if not m.ended]

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_send_move_update) > self.CLIENT_UPDATE_INTERVAL_MS:
            self.last_send_move_update = now
            msg = bytearray([self.client_id, ClientUpdate.MOVE])
            msg += struct.pack(
                '<eeeeeH',
                self.my_ship.x,
                self.my_ship.y,
                self.my_ship.vel,
                self.my_ship.vdir,
                self.my_ship.angular_velocity,
                self.my_ship.damage,
            )
            self.raw_msg_server_func(msg)

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
                self.my_ship.stardust += Star.STARDUST_VALUE
                log(f'Collected a star! Total stardust: {self.my_ship.stardust}')
        elif msg_type == BroadcastUpdate.SHIP_AND_MISSILE:
            idx = 1
            self.remaining_time = int.from_bytes(raw_data[idx:idx+4], 'little')
            idx += 4
            for i in range(self.num_ships):
                x, y, vel, vdir, angular_velocity, damage = struct.unpack('<eeeeeH', raw_data[idx:idx+12])
                idx += 12
                if i == self.client_id:
                    if not self.my_ship_position_initialized:
                        self.my_ship.x = x
                        self.my_ship.y = y
                        self.my_ship.vel = vel
                        self.my_ship.vdir = vdir
                        self.my_ship.angular_velocity = angular_velocity
                        self.my_ship.cos_a = math.cos(-vdir - math.pi/2)
                        self.my_ship.sin_a = math.sin(-vdir - math.pi/2)
                        self.my_ship_position_initialized = True
                        log(f'initialized my ship position to x={x}, y={y}')
                    if damage < self.my_ship.damage:
                        log('server damage lower than client, ignoring')
                    else:
                        self.my_ship.damage = damage
                elif self.other_ship is not None:
                    self.other_ship.x = x
                    self.other_ship.y = y
                    self.other_ship.vel = vel
                    self.other_ship.vdir = vdir
                    self.other_ship.cos_a = math.cos(-vdir - math.pi/2)
                    self.other_ship.sin_a = math.sin(-vdir - math.pi/2)
                    self.other_ship.damage = damage
            while idx + 9 <= len(raw_data):
                x, y, dir_, speed, exploded, missile_id, damage = struct.unpack('<eeeeBHB', raw_data[idx:idx+12])
                idx += 12
                # either create new missile or update existing one
                for missile in self.missiles:
                    if missile.id_ == missile_id:
                        # no need to update position or direction as it can be calculated from initial values
                        if exploded and missile.exploded is None:
                            missile.exploded = time.ticks_ms()
                        break
                else:
                    missile = Missile(x, y, dir_, speed, damage)
                    missile.id_ = missile_id
                    if exploded and missile.exploded is None:
                        missile.exploded = time.ticks_ms()
                    self.missiles.append(missile)


    def fire_missile(self):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_missile_launch) < 500:
            return
        self.last_missile_launch = current_time

        scaled_damage = 5 * math.log(self.ship_stats.stats['weapons'] + 1) + 40
        if scaled_damage > 100:
            scaled_damage = 100
        log(f'Firing missile with damage {scaled_damage:.1f}!')
        msg = bytearray([self.client_id, ClientUpdate.FIRE_MISSILE, int(scaled_damage)])
        self.raw_msg_server_func(msg)

    def draw(self, display):
        # background
        display.display.fill(TFT.color(10, 7, 89))

        # asteroids
        # NOTE: drawing these one by one is slow, consider batching
        for asteroid in self.asteroids:
            asteroid.draw(display.display, self.my_ship.apply_view_around_ship)

        # health bar
        display.display.fill_rect(40, 120, 100, 5, TFT.WHITE)
        health_ratio = (self.my_ship.max_health - self.my_ship.damage) / self.my_ship.max_health
        display.display.fill_rect(40, 120, int(100 * health_ratio), 5, TFT.RED)

        # stardust
        display.draw_text(0, 118, f'{self.my_ship.stardust:2}SD')

        # missiles
        for missile in self.missiles:
            missile.draw(display.display, self.my_ship.apply_view_around_ship)

        # stars
        # NOTE: drawing these one by one is slow, consider batching
        for star in self.stars:
            star.draw(display.display, self.my_ship.apply_view_around_ship)

        # other ship
        if self.other_ship is not None:
            self.other_ship.draw_other(display.display, self.my_ship.apply_view_around_ship)

        # ship
        self.my_ship.draw(display.display)

        # remaining time
        minutes = self.remaining_time // 60000
        seconds = (self.remaining_time % 60000) // 1000
        display.draw_text(80, 0, f'{minutes}:{seconds:02d}')


class AsteroidsGameClient(Runnable):
    CLIENT_TIMEOUT_MS = 500

    def __init__(self, device_io: "DeviceIO", wifi_client_id, wifi_client_send_fn, freeplay=False):
        self.device_io = device_io
        self.world = GameClient(wifi_client_id, self.device_io.ship_stats, freeplay=freeplay)
        self.world.raw_msg_server_func = wifi_client_send_fn
        self.joystick_x = 0
        self.joystick_y = 0
        self.last_update_time = time.ticks_ms()
        self.paused = False
        self.game_over = False
        self.last_recv_time = time.ticks_ms()
        self.freeplay = freeplay

    def wifi_recv_callback(self, msg):
        """
        Receive message from wifi and pass to client
        """
        self.last_recv_time = time.ticks_ms()
        if msg == b'GAME_OVER' and not self.game_over:
            self.end_game()
            return
        self.world.update_from_server(msg)

    def _update(self):
        current_time = time.ticks_ms()
        dt = time.ticks_diff(current_time, self.last_update_time)
        self.world.update(self.joystick_x, self.joystick_y, dt)
        self.last_update_time = current_time

    def _draw(self, fps=None):
        self.world.draw(self.device_io.display)
        if fps is not None:
            self.device_io.display.draw_text(0, 0, f'{fps:4.1f}FPS')
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

    async def _end_game_screen(self):
        health_bonus = int(max(0, self.world.my_ship.max_health - self.world.my_ship.damage) * 0.75)
        total_stardust = self.world.my_ship.stardust + health_bonus
        self.device_io.ship_stats.add_stardust(total_stardust)
        msgs = ['Game Over', '', f'Stardust found: {self.world.my_ship.stardust}', f'Health bonus: {health_bonus}', f'Total: {total_stardust}']
        if self.freeplay:
            msgs += [f'(not added to total', 'in freeplay mode)']
        await menu_with_text(
            self.device_io,
            msgs,
            [
                ('(scroll down)', None, None),
                ('Done', None, lambda: None)
            ]
        )

    def end_game(self):
        self.game_over = True
        self.world.raw_msg_server_func(b'GAME_OVER')

    async def run(self):
        self.device_io.joystick.subscribe(self._joystick_event, events=['xy'])
        self.device_io.buttons.subscribe(self._button_event, events=['a', 'b'])

        start_time = time.ticks_ms()
        num_frames = 0
        while not self.game_over:
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            num_frames += 1
            fps = num_frames * 1000 / elapsed if elapsed > 0 else 0

            self._update()
            self._draw(fps)

            await asyncio.sleep_ms(1)

            if self.world.my_ship.damage >= self.world.my_ship.max_health:
                self.end_game()

            if self.world.remaining_time <= 0:
                self.end_game()

            # timeout if no messages received for a while
            if time.ticks_diff(time.ticks_ms(), self.last_recv_time) > self.CLIENT_TIMEOUT_MS:
                log(f'No messages received from server for {self.CLIENT_TIMEOUT_MS} ms, ending game')
                self.end_game()

            if self.paused:
                async def updates():
                    while self.paused and not self.game_over:
                        self._update()
                        await asyncio.sleep_ms(1)

                await asyncio.gather(
                    menu_with_text(
                        self.device_io,
                        ['Game Paused'],
                        [
                            ('Resume', None, lambda: setattr(self, 'paused', False)),
                            ('End game', None, self.end_game),
                        ]
                    ),
                    updates()
                )

        self.device_io.joystick.unsubscribe(self._joystick_event, events=['xy'])
        self.device_io.buttons.unsubscribe(self._button_event, events=['a', 'b'])

        await self._end_game_screen()


class AsteroidsGameServerAndClient(Runnable):
    def __init__(self, device_io: "DeviceIO", wifi_client_id, wifi_server_send_fn, freeplay=False):
        self.server = GameServer(send_raw_msg_func=self._server_send_fn, freeplay=freeplay)
        self.client = AsteroidsGameClient(device_io, wifi_client_id, self._client_send_fn, freeplay=freeplay)
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

    def end_game(self):
        self.client.end_game()
        self.server.running = False

    async def run(self):
        server_task = asyncio.create_task(self.server.run())
        await self.client.run()
        self.server.running = False
        await server_task
