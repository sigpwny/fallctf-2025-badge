import asyncio
from logger import log


class MainController:
    def __init__(self, joystick, display):
        self.joystick = joystick
        self.display = display
        # TODO: subscribe to joystick events

    async def run(self):
        while True:
            await asyncio.sleep(1)
            log("MainController active")
