from ship_stats import ShipStats
from factions import FACTIONS
from battle import BattleRunner

ship1 = ShipStats(FACTIONS[0])
ship2 = ShipStats(FACTIONS[1])
ship3 = ShipStats(FACTIONS[2])

battle1 = BattleRunner(ship1.get_battle_stats(), ship2.get_battle_stats())
battle1.run()
print(battle1.ship1_chase_2_bonus)
print(battle1.ship2_chase_1_bonus)
print(battle1.damage_to_1)
print(battle1.damage_to_2)
print(battle1.ship1_won())
print(battle1.ship2_won())
print(battle1.is_tie())
