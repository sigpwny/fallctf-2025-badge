class Faction:
    def __init__(self, name: str, **boosts: int) -> None:
        self.name = name
        self.boosts = boosts


FACTION_UNDECIDED = Faction('undecided')
FACTION_WEAPONS = Faction('weapons faction', weapons=2)
FACTION_SHIELDS = Faction('shields faction', shields=2)
FACTION_THRUSTERS = Faction('thrusters faction', thrusters=2)
FACTION_SENSORS = Faction('sensors faction', sensors=2)
FACTIONS = [FACTION_UNDECIDED, FACTION_WEAPONS, FACTION_SHIELDS,
            FACTION_THRUSTERS, FACTION_SENSORS]
