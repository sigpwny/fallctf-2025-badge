from factions import Faction, FACTIONS
from battle import BattleStats, BattleRunner


def checksum(data: list[int]) -> int:
    ret = 0
    for x in data:
        ret ^= x
        ret += 0xFF55AA11
        ret &= 0xFFFFFFFF
    return ret


class ShipStats:
    def __init__(self, faction: Faction) -> None:
        self.total_stardust = 0
        self.stardust = 0
        self.resets = 0

        self.faction = faction
        self.weapons = 0
        self.shields = 0
        self.thrusters = 0
        self.sensors = 0

    def load_file(self, filename: str) -> None:
        data = []
        with open(filename) as f:
            for line in f:
                data.append(int(line))

        data, chk = data[:-1], data[-1]
        if chk != checksum(data):
            raise Exception(
                f'Loading file {filename} checksum failed. Possibly corrupted or modified save file.')

        self.total_stardust, self.stardust, self.resets, faction_idx, self.weapons, self.shields, self.thrusters, self.sensors = data
        self.faction = FACTIONS[faction_idx]

    def save_file(self, filename: str) -> None:
        faction_idx = FACTIONS.index(self.faction)
        data = [self.total_stardust, self.stardust, self.resets, faction_idx,
                self.weapons, self.shields, self.thrusters, self.sensors]

        chk = checksum(data)
        with open(filename, 'w') as f:
            for x in data:
                f.write(f'{x}\n')
            f.write(f'{chk}\n')

    def load(self) -> None:
        try:
            self.load_file('save1.txt')
            return
        except Exception as e:
            print(e)
        try:
            self.load_file('save2.txt')
            return
        except Exception as e:
            print(e)

    def save(self) -> None:
        self.save_file('save1.txt')
        self.save_file('save2.txt')

    def get_battle_stats(self) -> BattleStats:
        return BattleStats(
            weapons=self.weapons + self.faction.weapons_boost,
            shields=self.shields + self.faction.shields_boost,
            thrusters=self.thrusters + self.faction.thrusters_boost,
            sensors=self.sensors + self.faction.sensors_boost,
        )

    def receive_stardust(self, is_ship1: bool, battle: BattleRunner) -> None:
        self.stardust += 100
        if is_ship1 and battle.ship1_won() or not is_ship1 and battle.ship2_won():
            self.stardust += 50
        self.check_for_reset()

    def cost_to_upgrade(self, level: int) -> int:
        '''Returns the amount of stardust needed to upgrade to the given level'''
        return 100 + level * level

    def get_rank(self) -> str:
        # TODO rank class which determines how user is drawn
        if self.total_stardust <= 100:
            return 'Nebula'
        if self.total_stardust <= 500:
            return 'Protostar'
        if self.total_stardust <= 1000:
            return 'Massive Star'
        if self.total_stardust <= 2000:
            return 'Red Supergiant'
        if self.total_stardust <= 2200:
            return 'Supernova'
        return 'Black Hole'

    def check_for_reset(self) -> None:
        if self.get_rank() == 'Black Hole':
            self.total_stardust = 0
            self.stardust = 0
            self.resets += 1
