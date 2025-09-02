class Faction:
    def __init__(self, name: str, weapons_boost: int = 0, shields_boost: int = 0, thrusters_boost: int = 0, sensors_boost: int = 0) -> None:
        self.name = name
        # not very extendible, but not sure how to fix that
        self.weapons_boost = weapons_boost
        self.shields_boost = shields_boost
        self.thrusters_boost = thrusters_boost
        self.sensors_boost = sensors_boost


FACTION_UNDECIDED = Faction('undecided')
FACTION_WEAPONS = Faction('weapons faction', weapons_boost=2)
FACTION_SHIELDS = Faction('shields faction', shields_boost=2)
FACTION_THRUSTERS = Faction('thrusters faction', thrusters_boost=2)
FACTION_SENSORS = Faction('sensors faction', sensors_boost=2)
FACTIONS = [FACTION_UNDECIDED, FACTION_WEAPONS, FACTION_SHIELDS,
            FACTION_THRUSTERS, FACTION_SENSORS]
