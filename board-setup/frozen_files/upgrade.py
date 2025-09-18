from menu import Runnable, menu_with_text


TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO
    from menu import MenuItem


class UpgradeMenu(Runnable):
    def __init__(self, device_io: 'DeviceIO') -> None:
        self.device_io = device_io

    async def run(self):
        self.last_msg = ''
        self.keep_running = True
        self.prev_stats = (self.device_io.ship_stats.stardust, self.device_io.ship_stats.stats.copy())
        while self.keep_running:
            items: list[MenuItem] = []
            for s in ['weapons', 'shields', 'thrusters', 'sensors']:
                faction_buff = f' (+{self.device_io.ship_stats.faction.boosts[s]})' if s in self.device_io.ship_stats.faction.boosts else ''
                items.append((f'{s}: {self.device_io.ship_stats.stats[s]}{faction_buff}', None, self.upgrade_stat(s)))
            items.append(('confirm', None, self.confirm))
            items.append(('cancel', None, self.cancel))
            await menu_with_text(self.device_io, [f'StarDust: {self.device_io.ship_stats.stardust}', f'Cost: {self.device_io.ship_stats.cost_to_upgrade()}', self.last_msg], items, exit_on_b_handler=self.cancel)

    def confirm(self):
        self.keep_running = False

    def cancel(self):
        self.device_io.ship_stats.stardust, self.device_io.ship_stats.stats = self.prev_stats
        self.keep_running = False

    def undo(self):
        if self.prev_stats is not None:
            self.device_io.ship_stats.save()
            self.last_msg = 'Undid upgrade'
        self.prev_stats = None

    def upgrade_stat(self, stat: str):
        def upgrade_stat():
            if self.device_io.ship_stats.upgrade(stat):
                self.last_msg = f'Upgraded {stat}'
            else:
                self.last_msg = 'Not enough SD'
        return upgrade_stat
