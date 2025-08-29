from factions import Faction
from battle import BattleStats, BattleRunner

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

    def load(self) -> None:
        # TODO load from file
        pass

    def save(self) -> None:
        # TODO save to file (maybe include checksum?)
        pass

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
            # TODO give flag
            self.total_stardust = 0
            self.stardust = 0
            self.resets += 1
