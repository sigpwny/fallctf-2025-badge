import asyncio

from menu import Runnable, ListMenu
from view import BasicTextView
from layout import SimpleLayout
from battle import BattleRunner
from ship_stats import ShipStats

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class HostBattleMenu(Runnable):
    def __init__(self, device_io: 'DeviceIO'):
        self.device_io = device_io
        self.view = SimpleLayout(device_io.display, BasicTextView(device_io.display))

        # self.device_io.wifi.subscribe(self.wifi_event, events=['client_join'])
        # self.device_io.wifi.start_broadcasting()
        self.view.first_render()
        self.view.update(0, 'broadcasting...')
        self.view.render()

        self.waiting = True

    def wifi_event(self, event_type, data):
        pass

    def battle_event(self, event, battle):
        self.waiting = False

    async def simulate_connection(self, battle: BattleRunner):
        await asyncio.sleep(1)
        await battle.run()

    async def run(self):
        # simulate a client joining
        battle = BattleRunner(self.device_io, self.device_io.ship_stats.get_battle_stats(), ShipStats().get_battle_stats())
        battle.subscribe(self.battle_event, events=['result'])
        asyncio.create_task(self.simulate_connection(battle))

        while self.waiting:
            await asyncio.sleep(0.1)


class JoinBattleMenu(ListMenu):
    def __init__(self, device_io: 'DeviceIO'):
        super().__init__(device_io, [])

        # simulate a couple connections
        self.items.append(('id1', lambda: BattleRunner(self.device_io, self.device_io.ship_stats.get_battle_stats(), ShipStats().get_battle_stats())))
        self.items.append(('id2', lambda: BattleRunner(self.device_io, self.device_io.ship_stats.get_battle_stats(), ShipStats().get_battle_stats())))
        self.items.append(('id3', lambda: BattleRunner(self.device_io, self.device_io.ship_stats.get_battle_stats(), ShipStats().get_battle_stats())))

        # self.device_io.wifi.subscribe(self.wifi_event, events=['host_broadcast'])

    def wifi_event(self, event_type, data):
        pass
