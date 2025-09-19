import asyncio
from logger import Logger, set_logger, log
# NOTE: Do NOT add any more local imports! Dynamically import most modules in _start()


class Environment:
    def __init__(self, mode='dev'):
        assert mode in ['dev', 'test', 'prod'], "Mode must be 'dev', 'test', or 'prod'"

        import early_board_init
        self.early_board_init = early_board_init

        self.mode = mode
        set_logger(Logger(log_level=mode))

        self.device_io = None

    def run(self):
        log('Environment.run')
        try:
            asyncio.run(self._start())
        except Exception as e:
            if self.device_io is not None:
                text = f"Fatal error: {e}"
                log(text)
                self.device_io.display.clear()
                idx = 0
                for i in range(0, len(text), 20):
                    self.device_io.display.draw_text(0, i // 20 * 10, text[i:i+20])
                    idx += 1
                idx += 1
                self.device_io.display.draw_text(0, idx * 10, "Press back reset")
                idx += 1
                self.device_io.display.draw_text(0, idx * 10, "button to restart")
                self.device_io.display.show()
            raise e

    async def _start(self):
        from display import Display
        display = Display(_buffer=self.early_board_init.display_buffer)
        from boot_screen import boot_screen
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
        self.device_io = device_io

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
