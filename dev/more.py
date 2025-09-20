import esp32

from menu import Runnable, ListMenu
from flag_manager import FlagsMenu
from asteroids_game import AsteroidsGameServerAndClient
from invaders_game import InvadersGame
from intro_screen import IntroScreen


class MoreMenu(Runnable):
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io
        self._go_back = False

    async def run(self):
        menu = None
        while not self._go_back:
            menu_options = [
                ("back", None, lambda: setattr(self, "_go_back", True)),
                ("Free play", None, AsteroidsGameServerAndClient(self.device_io, 0, lambda _: None, freeplay=True)),
                ('Space Invaders', None, InvadersGame(self.device_io)),
                ("Flags", None, FlagsMenu(self.device_io)),
                ('Intro', None, IntroScreen(self.device_io)),
            ]
            menu = ListMenu(
                self.device_io,
                menu_options,
                init_selected=0 if menu is None else menu.select_idx,
                exit_on_b_handler=lambda: setattr(self, "_go_back", True),
                enable_render_cache=True,
            )
            await menu.run()
