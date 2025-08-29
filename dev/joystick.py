import asyncio
from logger import log


class Joystick:
    def __init__(self):
        pass

    async def run(self):
        while True:
            # Simulate joystick activity
            await asyncio.sleep(1)
            log("Joystick active")
