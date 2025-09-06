from view import BasicTextView
from layout import SimpleLayout
from ship_stats import ShipStats
from menu import ListMenu, Runnable
from debug_menu import DebugMenu

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO



class MainController:
    def __init__(self, device_io: 'DeviceIO'):
        self.device_io = device_io
        self.view = SimpleLayout(device_io.display, BasicTextView(device_io.display))


    async def run(self):
        while True:
            await ListMenu(self.device_io, [
                ('item1', lambda: Runnable()),
                ('item2', lambda: Runnable()),
                ('item3', lambda: Runnable()),
                ('qqq', lambda: Runnable()),
                ('aaaaaasdoipjefoi', lambda: Runnable()),
                ('debug', lambda: DebugMenu(self.device_io))
            ]).run()
            print('cannot exit main controller')
