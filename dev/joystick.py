import asyncio
from logger import log


class Joystick:
    def __init__(self):
        self.subscribers = {'xy': [], 'x': [], 'y': []}

    def subscribe(self, callback, events):
        """
        Subscribe to joystick events.
        :param callback: function to call on event
        :param events: event types to subscribe to ('xy': any movement, 'y': y-axis movement, 'x': x-axis movement)
        """
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].append(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    async def run(self):
        toggle = True
        while True:
            await asyncio.sleep(1)
            # TODO: Replace with actual joystick reading logic
            log("joystick event y")
            toggle = not toggle
            for callback in self.subscribers['y']:
                callback('y', 1 if toggle else -1)
