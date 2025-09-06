from view import BasicTextView
from layout import SimpleLayout
from ship_stats import ShipStats
from menu import ListMenu, Runnable
from debug_menu import DebugMenu


class MainController:
    def __init__(self, joystick, buttons, display):
        self.joystick = joystick
        self.buttons = buttons
        self.display = display
        self.view = SimpleLayout(display, BasicTextView(display))

        self.ship_stats = ShipStats()
        self.ship_stats.load()


    async def run(self):
        while True:
            await ListMenu(self.joystick, self.buttons, self. display, [
                ('item1', lambda: Runnable()),
                ('item2', lambda: Runnable()),
                ('item3', lambda: Runnable()),
                ('qqq', lambda: Runnable()),
                ('aaaaaasdoipjefoi', lambda: Runnable()),
                ('debug', lambda: DebugMenu(self.joystick,
                 self.buttons, self.display, self.ship_stats))
            ]).run()
            print('cannot exit main controller')
