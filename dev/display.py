import asyncio
from logger import log


class Display:
    def __init__(self):
        self.view_queue = asyncio.Queue()

    async def display(self, view):
        await self.view_queue.put(view)

    async def run(self):
        while True:
            view = await self.view_queue.get()
            # TODO: implement double buffering
