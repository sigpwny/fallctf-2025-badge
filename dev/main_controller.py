import asyncio
from logger import log
import time

from view import BasicTextView


class MainController:
    def __init__(self, joystick, display):
        self.joystick = joystick
        self.display = display
        self.view = BasicTextView(display=display)

        self.joystick.subscribe(self.joystick_event, events=['xy', 'up-down', 'left-right'])
        self.view.first_render()

    def joystick_event(self, event_type, value):
        if event_type == 'xy':
            x, y = value['x'], value['y']
            self.view.update(0, f'joystick:')
            self.view.update(1, f'x={x:.2f}, y={y:.2f}')
            self.view.render()
        elif event_type == 'up-down':
            self.view.update(2, f'up-down: {"down" if value else "up  "}')
            self.view.render()
        elif event_type == 'left-right':
            self.view.update(3, f'left-right: {"right" if value else "left "}')
            self.view.render()

    async def run(self):
        while True:
            self.view.update(5, f'Time: {time.time_ns()/1e9:.2f} s')
            self.view.update(6, f'Updates: {self.view.get_renders_per_second():.2f} r/s')
            self.view.render()
            await asyncio.sleep(0.1)
