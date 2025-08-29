import random


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
        self.ship1 = ship1
        self.ship2 = ship2

    def run(self) -> None:
        self.ship1_chase_2_bonus = run_chase(self.ship1, self.ship2)
        self.damage_to_2 = run_attack(
            self.ship1, self.ship2, self.ship1_chase_2_bonus)
        self.ship2_chase_1_bonus = run_chase(self.ship2, self.ship1)
        self.damage_to_1 = run_attack(
            self.ship2, self.ship1, self.ship2_chase_1_bonus)

    def ship1_won(self) -> bool:
        return self.damage_to_1 < self.damage_to_2

    def ship2_won(self) -> bool:
        return self.damage_to_1 > self.damage_to_2

    def is_tie(self) -> bool:
        return self.damage_to_1 == self.damage_to_2
