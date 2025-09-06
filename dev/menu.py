import asyncio

from view import BasicTextView
from layout import SimpleLayout


TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Callable
    from device_io import DeviceIO


class Runnable:
    async def run(self):
        pass


class ListMenu(Runnable):
    def __init__(self, device_io: 'DeviceIO', items: 'list[tuple[str, Callable[[], Runnable]]]'):
        self.device_io = device_io
        self.view = SimpleLayout(device_io. display, BasicTextView(device_io.display))

        self.device_io.joystick.subscribe(self.joystick_event, events=['up-down'])
        self.device_io.buttons.subscribe(self.button_event, events=['a', 'b'])
        self.view.first_render()

        # cannot have 0 items
        self.items = items or [('no items', lambda: Runnable())]
        self.keep_running = True
        self.item_selected = False
        self.select_idx = 0

    def joystick_event(self, event_type, value):
        if event_type == 'up-down':
            if value:
                self.select_idx = (self.select_idx - 1) % len(self.items)
            else:
                self.select_idx = (self.select_idx + 1) % len(self.items)

    def button_event(self, button, pressed):
        if not pressed:
            return
        if button == 'a':
            self.item_selected = True
        self.keep_running = False

    async def run(self):
        while self.keep_running:
            for i, (name, item) in enumerate(self.items):
                line = f'> {name}' if i == self.select_idx else f'  {name}'
                self.view.update(i, line)
            self.view.render()
            await asyncio.sleep(0.1)
        if self.item_selected:
            await self.items[self.select_idx][1]().run()
