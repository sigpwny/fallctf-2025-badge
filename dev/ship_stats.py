import errno

from logger import log
from factions import FACTIONS, FACTION_UNDECIDED
from battle import BattleStats, BattleRunner


def checksum(data: list[int]) -> int:
    ret = 0
    for x in data:
        ret ^= x
        ret += 0xFF55AA11
        ret &= 0xFFFFFFFF
    return ret


class ShipStats:
    def __init__(self) -> None:
        self.stardust = 0
        self.resets = 0

        self.faction = FACTION_UNDECIDED
        self.stats = {'weapons': 0, 'shields': 0, 'thrusters': 0, 'sensors': 0}

    def load_file(self, filename: str) -> None:
        data = []
        with open(filename) as f:
            for line in f:
                data.append(int(line))

        data, chk = data[:-1], data[-1]
        if chk != checksum(data):
            raise Exception(
                f'Loading file {filename} checksum failed. Possibly corrupted or modified save file.')

        self.stardust, self.resets, faction_idx, self.stats['weapons'], self.stats['shields'], self.stats['thrusters'], self.stats['sensors'] = data
        self.faction = FACTIONS[faction_idx]

    def save_file(self, filename: str) -> None:
        faction_idx = FACTIONS.index(self.faction)
        data = [self.stardust, self.resets, faction_idx,
                self.stats['weapons'], self.stats['shields'], self.stats['thrusters'], self.stats['sensors']]

        chk = checksum(data)
        with open(filename, 'w') as f:
            for x in data:
                f.write(f'{x}\n')
            f.write(f'{chk}\n')

    def load(self) -> None:
        try:
            self.load_file('save1.txt')
            return
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        except Exception as e:
            log(e, level='prod')
        try:
            self.load_file('save2.txt')
            return
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        except Exception as e:
            log(e, level='prod')

    def save(self) -> None:
        self.save_file('save1.txt')
        self.save_file('save2.txt')

    def get_battle_stats(self) -> BattleStats:
        return BattleStats(
            weapons=self.stats['weapons'] + self.faction.boosts.get('weapons', 0),
            shields=self.stats['shields'] + self.faction.boosts.get('shields', 0),
            thrusters=self.stats['thrusters'] + self.faction.boosts.get('thrusters', 0),
            sensors=self.stats['sensors'] + self.faction.boosts.get('sensors', 0),
        )

    def receive_stardust(self, won: bool) -> int:
        stardust_received = 100
        if won:
            stardust_received += 50
        self.stardust += stardust_received
        self.save()
        return stardust_received

    def upgrade(self, stat: str) -> bool:
        if self.stardust >= self.cost_to_upgrade():
            self.stardust -= self.cost_to_upgrade()
            self.stats[stat] += 1
            self.save()
            return True
        else:
            return False

    def cost_to_upgrade(self) -> int:
        '''Returns the amount of stardust needed to upgrade from the given level'''
        levels = sum(self.stats.values())
        return (10 + levels) ** 2
