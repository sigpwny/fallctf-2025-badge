from view import BasicTextView
from layout import SimpleLayout
from menu import ListMenu
from debug_menu import DebugMenu
from debug_wireless import WirelessDebug
from battle_menu import HostBattleMenu, JoinBattleMenu
from circling_ship import CirclingShip
from layout import Style

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class MainController:
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io
        self.view = SimpleLayout(device_io.display, BasicTextView(device_io.display))

    async def run(self):
        while True:
            await ListMenu(
                self.device_io,
                [
                    (
                        "debug",
                        [
                            ("peripheral debug", None, lambda: DebugMenu(self.device_io)),
                            ("wireless debug", None, lambda: WirelessDebug(self.device_io)),
                        ],
                        None,
                    ),
                    (
                        "battle",
                        [
                            ("host", None, lambda: HostBattleMenu(self.device_io)),
                            ("join", None, lambda: JoinBattleMenu(self.device_io)),
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
