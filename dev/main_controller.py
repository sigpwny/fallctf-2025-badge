import asyncio
from logger import log
import time

from view import BasicTextView


class MainController:
    def __init__(self, joystick, display):
        self.joystick = joystick
        self.display = display
        self.view = BasicTextView(display=display)

        self.joystick.subscribe(self.joystick_event, events=['y'])
        self.view.first_render()

    def joystick_event(self, event_type, value):
        log(f'MainController.joystick_event({event_type}, {value})')
        self.view.update(0, f'Joystick {event_type}: {value} (sim)')
        self.view.render()

    async def run(self):
        while True:
            self.view.update(1, f'Time: {time.time_ns()/1e9:.2f} s')
            self.view.render()
            await asyncio.sleep(0.1)
