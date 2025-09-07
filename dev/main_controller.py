from view import BasicTextView
from layout import SimpleLayout
from menu import ListMenu, Runnable
from debug_menu import DebugMenu
from battle_menu import HostBattleMenu, JoinBattleMenu

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
                    ("debug", None, lambda: DebugMenu(self.device_io)),
                    (
                        "battle",
                        [
                            ("host", None, lambda: HostBattleMenu(self.device_io)),
                            ("join", None, lambda: JoinBattleMenu(self.device_io)),
                        ],
                        None,
                    ),
                ],
            ).run()
