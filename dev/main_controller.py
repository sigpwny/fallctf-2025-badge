from view import BasicTextView
from menu import ListMenu, ImageMenu, menu_with_text
from circling_ship import CirclingShip
from color_test import ColorTest
from layout import Style
import wireless
from connect import ConnectMenu
from upgrade import UpgradeMenu
from settings import SettingsMenu

from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class MainController:
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io

    async def run(self):
        log('MainController started')
        while True:
            await ImageMenu(
                self.device_io,
                [
                    'assets/first_page_1.raw',
                    'assets/first_page_2.raw',
                    'assets/first_page_3.raw',
                ],
                [
                    ConnectMenu(self.device_io),
                    UpgradeMenu(self.device_io),
                    SettingsMenu(self.device_io),
                ]
            ).run()
