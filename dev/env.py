import asyncio

from logger import Logger, set_logger, log
from boot_screen import boot_screen

# dynamically import most modules


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
        from joystick import Joystick
        from main_controller import MainController

        joystick = Joystick()
        if self.boardless_mode:
            from soft_display import SoftDisplay
            display = SoftDisplay()
        else:
            from display import Display
            if self.early_board_init is None:
                raise RuntimeError("early_board_init is required for non-boardless mode")
            display = Display(_buffer=self.early_board_init.display_buffer)
            # boot screen
            boot_screen(display)
        main_controller = MainController(joystick=joystick, display=display)

        await asyncio.gather(
            main_controller.run(),
            display.run(),
            joystick.run()
        )
