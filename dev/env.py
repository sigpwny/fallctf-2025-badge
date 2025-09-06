import asyncio
from logger import Logger, set_logger, log
# NOTE: Do NOT add any more local imports! Dynamically import most modules in _start()


class Environment:
    def __init__(self, mode='dev', boardless_mode=False):
        assert mode in ['dev', 'test', 'prod'], "Mode must be 'dev', 'test', or 'prod'"
        self.boardless_mode = boardless_mode
        if not self.boardless_mode:
            import early_board_init
            self.early_board_init = early_board_init
        else:
            self.early_board_init = None
        self.mode = mode
        set_logger(Logger(log_level=mode))

    def run(self):
        log('Environment.run')
        asyncio.run(self._start())

    async def _start(self):
        if self.boardless_mode:
            from soft_display import SoftDisplay
            display = SoftDisplay()
        else:
            from display import Display
            if self.early_board_init is None:
                raise RuntimeError("early_board_init is required for non-boardless mode")
            display = Display(_buffer=self.early_board_init.display_buffer)
            from boot_screen import boot_screen
            # boot screen
            boot_screen(display)

        from joystick import Joystick
        from buttons import Buttons
        from accelerometer import Accelerometer
        from main_controller import MainController
        from device_io import DeviceIO
        from ship_stats import ShipStats

        joystick = Joystick()
        buttons = Buttons()
        accelerometer = Accelerometer()
        ship_stats = ShipStats()
        ship_stats.load()
        device_io = DeviceIO(joystick, buttons, accelerometer, display, ship_stats)
        main_controller = MainController(device_io)

        await asyncio.gather(
            main_controller.run(),
            display.run(),
            joystick.run(),
            buttons.run(),
            accelerometer.run(),
        )
