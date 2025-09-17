import random
import asyncio

from layout import SimpleLayout
from view import BasicTextView
from menu import Runnable, menu_with_text

from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class BattleStats:
    def __init__(self, weapons: int, shields: int, thrusters: int, sensors: int) -> None:
        self.weapons = weapons
        self.shields = shields
        self.thrusters = thrusters
        self.sensors = sensors

    def serialize(self) -> bytes:
        if not all(-(1<<31) <= stat < (1<<31) for stat in (self.weapons, self.shields, self.thrusters, self.sensors)):
            raise ValueError('BattleStats values must be 32-bit signed integers')
        # serialize as 4 bytes each, little-endian
        data = bytearray(16)
        for i, stat in enumerate((self.weapons, self.shields, self.thrusters, self.sensors)):
            data[i*4:(i+1)*4] = stat.to_bytes(4, 'little')
        return bytes(data)

    @staticmethod
    def deserialize(data: bytes) -> 'BattleStats':
        if len(data) != 16:
            raise ValueError('Invalid data length for BattleStats deserialization')
        stats = []
        for i in range(4):
            stat = int.from_bytes(data[i*4:(i+1)*4], 'little')
            stats.append(stat)
        return BattleStats(*stats)

    def __repr__(self) -> str:
        return f'BattleStats(weapons={self.weapons}, shields={self.shields}, thrusters={self.thrusters}, sensors={self.sensors})'


def run_chase(attacker: BattleStats, defender: BattleStats) -> int:
    return attacker.sensors - defender.thrusters + random.randint(-10, 10)


def run_attack(attacker: BattleStats, defender: BattleStats, chase_bonus: int) -> int:
    return attacker.weapons - defender.shields + random.randint(-10 + min(0, chase_bonus),
                                                                10 + max(0, chase_bonus))


class BattleRunner(Runnable):
    def __init__(self, device_io: 'DeviceIO', ship1: BattleStats, ship2: BattleStats, view: SimpleLayout | None = None) -> None:
        log(f'BattleRunner: {ship1=}, {ship2=}')
        self.subscribers = {'result': []}
        self.ship1 = ship1
        self.ship2 = ship2
        self.device_io = device_io
        self.view = view or SimpleLayout(device_io.display, BasicTextView(device_io.display))


    def subscribe(self, callback, events):
        """
        Subscribe to battle events.
        :param callback: function to call on event
        :param events: event types to subscribe to ('result',)
        """
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].append(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    def unsubscribe(self, callback, events):
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].remove(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    async def run(self, switch_side=False, seed: int | None = None, opp: bytes = b'ffffffffffff'):
        # generate all values ahead of time since we are seeding the PRNG
        if seed is not None:
            log(f'Seeding battle with {seed}')
            random.seed(seed)
        self.ship1_chase_2_bonus = run_chase(self.ship1, self.ship2)
        self.damage_to_2 = run_attack(self.ship1, self.ship2, self.ship1_chase_2_bonus)
        self.ship2_chase_1_bonus = run_chase(self.ship2, self.ship1)
        self.damage_to_1 = run_attack(self.ship2, self.ship1, self.ship2_chase_1_bonus)

        my_side = 'me' if not switch_side else 'other'
        other_side = 'other' if not switch_side else 'me'
        msgs = [
            'Running battle...',
            '(values indicate HP gained/lost)',
            f'{my_side} chase {other_side}: {self.ship1_chase_2_bonus}',
            f'{my_side} attack {other_side}: {self.damage_to_2}',
            f'{other_side} chase {my_side}: {self.ship2_chase_1_bonus}',
            f'{other_side} attack {my_side}: {self.damage_to_1}',
        ]

        win_msg = ''
        if self.is_tie():
            sd_recv = self.device_io.ship_stats.receive_stardust(won=False, opp=opp)
            win_msg = f'tie (+{sd_recv} SD)'
        elif self.ship1_won() and not switch_side or self.ship2_won() and switch_side:
            sd_recv = self.device_io.ship_stats.receive_stardust(won=True, opp=opp)
            win_msg = f'you win! (+{sd_recv} SD)'
        else:
            sd_recv = self.device_io.ship_stats.receive_stardust(won=False, opp=opp)
            win_msg = f'you lose! (+{sd_recv} SD)'

        self.view.first_render()
        for i, msg in enumerate(msgs):
            self.view.update(i, msg)
            self.view.render()
            await asyncio.sleep_ms(500)

        for callback in self.subscribers['result']:
            callback('result', self)

        # note: we can't have no action because that is used for submenus
        # we use an empty lambda instead
        await menu_with_text(self.device_io, msgs + [win_msg], [('OK', None, lambda: None)])


    def ship1_won(self) -> bool:
        return self.damage_to_1 < self.damage_to_2

    def ship2_won(self) -> bool:
        return self.damage_to_1 > self.damage_to_2

    def is_tie(self) -> bool:
        return self.damage_to_1 == self.damage_to_2
