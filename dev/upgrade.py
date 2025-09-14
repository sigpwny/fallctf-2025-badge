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
        self.device_io.buttons.subscribe(self.button_event, events=['b'])
        self.prev_stats = None
        while self.keep_running:
            items: list[MenuItem] = []
            for s in ['weapons', 'shields', 'thrusters', 'sensors']:
                faction_buff = f' (+{self.device_io.ship_stats.faction.boosts[s]})' if s in self.device_io.ship_stats.faction.boosts else ''
                items.append((f'{s}: {self.device_io.ship_stats.stats[s]}{faction_buff}', None, self.upgrade_stat(s)))
            if self.prev_stats is not None:
                items.append(('undo', None, self.undo))
            await menu_with_text(self.device_io, [f'StarDust: {self.device_io.ship_stats.stardust}', f'Cost: {self.device_io.ship_stats.cost_to_upgrade()}', self.last_msg], items)
        self.device_io.buttons.unsubscribe(self.button_event, events=['b'])

    def button_event(self, button, pressed):
        if button == 'b' and pressed:
            self.keep_running = False

    def undo(self):
        if self.prev_stats is not None:
            self.device_io.ship_stats.stardust, self.device_io.ship_stats.stats = self.prev_stats
            self.device_io.ship_stats.save()
            self.last_msg = 'Undid upgrade'
        self.prev_stats = None

    def upgrade_stat(self, stat: str):
        def upgrade_stat():
            prev_stats = (self.device_io.ship_stats.stardust, self.device_io.ship_stats.stats.copy())
            if self.device_io.ship_stats.upgrade(stat):
                self.last_msg = f'Upgraded {stat}'
                self.prev_stats = prev_stats
            else:
                self.last_msg = 'Not enough SD'
        return upgrade_stat
