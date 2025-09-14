from view import BasicTextView
from menu import ListMenu, menu_with_text
# from debug_menu import DebugMenu
# from debug_wireless import WirelessDebug
from circling_ship import CirclingShip
from color_test import ColorTest
from layout import Style
import wireless
from connect import ConnectMenu
from upgrade import UpgradeMenu

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
            await ListMenu(
                self.device_io,
                [
                    ("connect", None, ConnectMenu(self.device_io)),
                    ("upgrade", None, UpgradeMenu(self.device_io)),
                    (
                        "debug",
                        [
                            # ("peripheral debug", None, DebugMenu(self.device_io)),
                            # ("wireless debug", None, WirelessDebug(self.device_io)),
                        ],
                        None,
                    ),
                ],
                additional_views=[
                    (
                        CirclingShip(self.device_io.display, height=40),
                        Style(posType=0b01, x=0, y=5),
                    ),
                    (
                        ColorTest(self.device_io.display, height=20),
                        Style(posType=0b01, x=0, y=5),
                    )
                ],
            ).run()
