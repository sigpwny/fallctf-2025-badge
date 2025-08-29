import asyncio

from logger import Logger, set_logger, log
from joystick import Joystick
from display import Display
from main_controller import MainController


class Environment:
    def __init__(self, mode='dev'):
        assert mode in ['dev', 'test', 'prod'], "Mode must be 'dev', 'test', or 'prod'"
        self.mode = mode
        set_logger(Logger(log_level=mode))

    def run(self):
        log('Environment.run')
        asyncio.run(self._start())

    async def _start(self):
        joystick = Joystick()
        display = Display()
        main_controller = MainController(joystick=joystick, display=display)

        await asyncio.gather(
            main_controller.run(),
            display.run(),
            joystick.run()
        )
