from factions import Faction
from battle import BattleStats


class ShipStats:
    def __init__(self, faction: Faction) -> None:
        self.stardust = 0
        self.faction = faction
        self.weapons = 0
        self.shields = 0
        self.thrusters = 0
        self.sensors = 0

    def get_battle_stats(self) -> BattleStats:
        return BattleStats(
            weapons=self.weapons + self.faction.weapons_boost,
            shields=self.shields + self.faction.shields_boost,
            thrusters=self.thrusters + self.faction.thrusters_boost,
            sensors=self.sensors + self.faction.sensors_boost,
        )
