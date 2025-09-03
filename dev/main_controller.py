import asyncio
from logger import log
import time

from view import BasicTextView
from layout import SimpleLayout
from ship_stats import ShipStats
from factions import FACTION_UNDECIDED, FACTION_WEAPONS
from battle import BattleRunner


class MainController:
    def __init__(self, joystick, buttons, display):
        self.joystick = joystick
        self.buttons = buttons
        self.display = display
        self.view = SimpleLayout(display, BasicTextView(display))

        self.joystick.subscribe(self.joystick_event, events=['xy', 'up-down', 'left-right'])
        self.buttons.subscribe(self.button_event, events=['a', 'b'])
        self.view.first_render()

        self.ship_stats = ShipStats(FACTION_WEAPONS)
        self.ship_stats.load()

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
        self.view.update(4, f'button {button}: {"pressed" if pressed else "released"}')
        self.view.render()

        if button == 'a' and pressed:
            # test out battle stuff
            other_ship = ShipStats(FACTION_UNDECIDED)
            battle = BattleRunner(
                self.ship_stats.get_battle_stats(), other_ship.get_battle_stats())
            battle.subscribe(self.battle_event, events=['result'])
            asyncio.create_task(battle.run(self.view))
        if button == 'b' and pressed:
            # testing upgrades
            if self.ship_stats.stardust >= self.ship_stats.cost_to_upgrade(self.ship_stats.weapons):
                self.ship_stats.stardust -= self.ship_stats.cost_to_upgrade(
                    self.ship_stats.weapons)
                self.ship_stats.weapons += 1
                self.ship_stats.save()
                self.view.update(
                    8, f'upgr W to {self.ship_stats.weapons}')
            else:
                self.view.update(8, f'not enough SD')
                self.view.update(
                    9, f'(have {self.ship_stats.stardust}, need {self.ship_stats.cost_to_upgrade(self.ship_stats.weapons)})')

    def battle_event(self, event, battle):
        stardust_received = self.ship_stats.receive_stardust(True, battle)
        self.view.update(9, f'received {stardust_received} stardust')

    async def run(self):
        while True:
            self.view.update(5, f'Time: {time.time_ns()/1e9:.2f} s')
            self.view.update(6, f'Updates: {self.view.get_renders_per_second():.2f} r/s')
            self.view.render()
            await asyncio.sleep(0.1)
