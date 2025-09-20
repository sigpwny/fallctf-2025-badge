from view import BasicTextView
from menu import ListMenu, HomeMenu, menu_with_text
from layout import Style
import wireless
from connect import ConnectMenu
from upgrade import UpgradeMenu
from settings import SettingsMenu
from more import MoreMenu
from intro_screen import IntroScreen

from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class MainController:
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io

    async def run(self):
        log('MainController started')
        if self.device_io.ship_stats.show_intro:
            await IntroScreen(self.device_io).run()
        self.device_io.ship_stats.show_intro = 0
        self.device_io.ship_stats.save()

        print('fallctf{s1gpwny_m4k3s_h4rdwar3!}')

        log('MainController main loop')
        while True:
            await HomeMenu(
                self.device_io,
                [
                    ConnectMenu(self.device_io),
                    UpgradeMenu(self.device_io),
                    MoreMenu(self.device_io),
                    SettingsMenu(self.device_io),
                ]
            ).run()
