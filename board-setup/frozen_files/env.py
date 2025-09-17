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
        from power import PowerMonitor
        from main_controller import MainController
        from device_io import DeviceIO
        from ship_stats import ShipStats
        from wireless import Wireless
        from speaker import Speaker
        from settings import Persist
        from flag_manager import add_installed_flags

        joystick = Joystick()
        buttons = Buttons()
        accelerometer = Accelerometer()
        power = PowerMonitor()
        ship_stats = ShipStats()
        ship_stats.load()
        if self.early_board_init is None:
            raise RuntimeError("wireless has not been initialized")
        wireless = Wireless(self.early_board_init.sta, self.early_board_init.esp)
        persist = Persist()
        add_installed_flags(persist)
        speaker = Speaker(persist)
        device_io = DeviceIO(joystick, buttons, accelerometer, power, display, ship_stats, wireless, speaker, persist)
        main_controller = MainController(device_io)

        speaker.success_sound()
        await asyncio.gather(
            main_controller.run(),
            display.run(),
            joystick.run(),
            buttons.run(),
            accelerometer.run(),
            power.run(),
            wireless.run(),
            speaker.run(),
        )
