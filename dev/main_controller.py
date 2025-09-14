from view import BasicTextView
from menu import ListMenu
# from debug_menu import DebugMenu
# from debug_wireless import WirelessDebug
from battle_menu import HostBattleMenu, JoinBattleMenu
from circling_ship import CirclingShip
from layout import Style
from connect import ConnectMenu

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
                    (
                        "debug",
                        [
                            # ("peripheral debug", None, DebugMenu(self.device_io)),
                            # ("wireless debug", None, WirelessDebug(self.device_io)),
                        ],
                        None,
                    ),
                    (
                        "battle",
                        [
                            # ("host", None, HostBattleMenu(self.device_io)),
                            # ("join", None, JoinBattleMenu(self.device_io)),
                        ],
                        None,
                    ),
                ],
                additional_views=[
                    (
                        CirclingShip(self.device_io.display, height=50),
                        # cannot use relative positioning here due to if menu unfolds
                        Style(posType=0b00, x=0, y=70),
                    )
                ],
            ).run()
