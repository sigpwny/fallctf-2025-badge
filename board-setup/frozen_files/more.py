import asyncio
import esp32

from menu import Runnable, ListMenu, menu_with_text_runnable
from flag_manager import FlagsMenu
from asteroids_game import AsteroidsGameServerAndClient
from invaders_game import InvadersGame
from intro_screen import IntroScreen


class SponsorsMenu(Runnable):
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io
        self.running = False

    def button_event(self, button, pressed):
        if pressed:
            self.running = False

    async def run(self):
        self.device_io.buttons.subscribe(self.button_event, events=["a", "b"])
        self.running = True

        old_backlight = self.device_io.display.display.backlight.duty_u16()
        self.device_io.display.display.set_backlight(0.8)

        self.device_io.display.draw_fullscreen_image('assets/sponsors.raw')
        self.device_io.display.draw_text(0, 10, 'Thank you')
        self.device_io.display.draw_text(0, 20, 'to our')
        self.device_io.display.draw_text(0, 30, 'sponsors')
        self.device_io.display.show()

        while self.running:
            await asyncio.sleep_ms(100)

        self.device_io.display.display.backlight.duty_u16(old_backlight)
        self.device_io.buttons.unsubscribe(self.button_event, events=["a", "b"])


class MoreMenu(Runnable):
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io
        self._go_back = False

    async def run(self):
        menu = None
        while not self._go_back:
            menu_options = [
                ("back", None, lambda: setattr(self, "_go_back", True)),
                ('Sponsors', None, SponsorsMenu(self.device_io)),
                (
                    'Credits',
                    None,
                    menu_with_text_runnable(
                        self.device_io,
                        [
                            'Thank you to all who',
                            'helped on the badge:',
                            '',
                            'Richard Liu (@rliu)',
                            '@32121',
                            '@e_ritque.arcus',
                            '@hackoverflow',
                            '@why0377',
                        ],
                        [('Ok', None, lambda: None)]
                    )
                ),
                ('Free Play', None, AsteroidsGameServerAndClient(self.device_io, 0, lambda _: None, freeplay=True)),
                (
                    'Space Invaders',
                    None,
                    menu_with_text_runnable(
                        self.device_io,
                        [
                            'Tilt your badge to',
                            'evade the aliens.',
                            'Use the joystick to',
                            'aim and "A" to',
                            'shoot. Press "B" to',
                            'exit. Good luck!',
                        ],
                        [
                            ('Start', None, InvadersGame(self.device_io)),
                            ('Back', None, lambda: None)
                        ]
                    )
                ),
                ('Flags', None, FlagsMenu(self.device_io)),
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
