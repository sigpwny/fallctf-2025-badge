import asyncio
import time

from view import BasicTextView
from layout import SimpleLayout
from battle import BattleRunner
from menu import Runnable
from ship_stats import ShipStats

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class DebugMenu(Runnable):
    def __init__(self, device_io: 'DeviceIO'):
        self.device_io = device_io
        self.view = SimpleLayout(device_io.display, BasicTextView(device_io.display))

        self.device_io.joystick.subscribe(self.joystick_event, events=[
                                'xy', 'up-down', 'left-right'])
        self.device_io.buttons.subscribe(self.button_event, events=['a', 'b'])
        self.device_io.accelerometer.subscribe(self.accel_event, events=['xyz'])
        self.view.first_render()

    def joystick_event(self, event_type, value):
        if event_type == 'xy':
            x, y = value['x'], value['y']
            self.view.update(0, f'joystick:')
            self.view.update(1, f'x={x:.2f}, y={y:.2f}')
            self.view.render()
        elif event_type == 'up-down':
            self.view.update(2, f'up-down: {"up" if value else "down"}')
            self.view.render()
        elif event_type == 'left-right':
            self.view.update(3, f'left-right: {"right" if value else "left"}')
            self.view.render()

    def button_event(self, button, pressed):
        self.view.update(
            4, f'button {button}: {"pressed" if pressed else "released"}')
        self.view.render()

        if button == 'a' and pressed:
            # test out battle stuff
            other_ship = ShipStats()
            battle = BattleRunner(
                self.device_io.ship_stats.get_battle_stats(), other_ship.get_battle_stats())
            battle.subscribe(self.battle_event, events=['result'])
            asyncio.create_task(battle.run(self.view))
        if button == 'b' and pressed:
            # testing upgrades
            cost_to_upgrade = self.device_io.ship_stats.cost_to_upgrade()
            if self.device_io.ship_stats.upgrade('weapons'):
                self.view.update(
                    8, f'upgr W to {self.device_io.ship_stats.stats['weapons']}')
                self.view.update(
                    9, f'{self.device_io.ship_stats.stardust} (-{cost_to_upgrade}) SD')
            else:
                self.view.update(8, f'not enough SD')
                self.view.update(
                    9, f'(have {self.device_io.ship_stats.stardust}, need {self.device_io.ship_stats.cost_to_upgrade()})')
 
    def accel_event(self, event_type, value):
        if event_type == 'xyz':
            x, y, z = value['x'], value['y'], value['z']
            self.view.update(7, f'{x:+.2f} {y:+.2f} {z:+.2f}')
            self.view.render()

    def battle_event(self, event, battle):
        stardust_received = self.device_io.ship_stats.receive_stardust(True, battle)
        self.view.update(
            9, f'{self.device_io.ship_stats.stardust} (+{stardust_received}) SD')

    async def run(self):
        while True:
            self.view.update(5, f'Time: {time.time_ns()/1e9:.2f} s')
            self.view.update(
                6, f'Updates: {self.view.get_renders_per_second():.2f} r/s')
            self.view.update(10, f'Power: {int(self.device_io.power.get_power_draw()):3} mW, {self.device_io.power.get_battery_percentage()}%')
            self.view.render()
            await asyncio.sleep_ms(200)
