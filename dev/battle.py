import random
import asyncio

from view import BasicTextView


class BattleStats:
    def __init__(self, weapons: int, shields: int, thrusters: int, sensors: int) -> None:
        self.weapons = weapons
        self.shields = shields
        self.thrusters = thrusters
        self.sensors = sensors


def run_chase(attacker: BattleStats, defender: BattleStats) -> int:
    return attacker.sensors - defender.thrusters + random.randint(-10, 10)


def run_attack(attacker: BattleStats, defender: BattleStats, chase_bonus: int) -> int:
    return attacker.weapons - defender.shields + random.randint(-10 + min(0, chase_bonus),
                                                                10 + max(0, chase_bonus))


class BattleRunner:
    def __init__(self, ship1: BattleStats, ship2: BattleStats) -> None:
        self.subscribers = {'result': []}
        self.ship1 = ship1
        self.ship2 = ship2

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

    async def run(self, view: BasicTextView) -> None:
        view.update(8, f'Running battle...')

        await asyncio.sleep(1)
        self.ship1_chase_2_bonus = run_chase(self.ship1, self.ship2)
        view.update(8, f'1 chase 2: {self.ship1_chase_2_bonus}...')

        await asyncio.sleep(1)
        self.damage_to_2 = run_attack(
            self.ship1, self.ship2, self.ship1_chase_2_bonus)
        view.update(8, f'1 attack 2: {self.damage_to_2}...')

        await asyncio.sleep(1)
        self.ship2_chase_1_bonus = run_chase(self.ship2, self.ship1)
        view.update(8, f'2 chase 1: {self.ship2_chase_1_bonus}...')

        await asyncio.sleep(1)
        self.damage_to_1 = run_attack(
            self.ship2, self.ship1, self.ship2_chase_1_bonus)
        view.update(8, f'2 attack 1: {self.damage_to_1}...')

        await asyncio.sleep(1)
        if self.ship1_won():
            view.update(8, f'result: ship 1 won')
        if self.ship2_won():
            view.update(8, f'result: ship 2 won')
        if self.is_tie():
            view.update(8, f'result: tie')

        await asyncio.sleep(1)
        for callback in self.subscribers['result']:
            callback('result', self)

    def ship1_won(self) -> bool:
        return self.damage_to_1 < self.damage_to_2

    def ship2_won(self) -> bool:
        return self.damage_to_1 > self.damage_to_2

    def is_tie(self) -> bool:
        return self.damage_to_1 == self.damage_to_2
