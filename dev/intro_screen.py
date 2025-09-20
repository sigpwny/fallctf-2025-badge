import asyncio

from layout import SimpleLayout
from view import BasicTextView
from menu import Runnable

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


MESSAGE = '''Welcome to the
FallCTF badge!

Connect and battle
others to earn
StarDust (SD),
which you can spend
for upgrades (and
maybe get a flag!)

Battle new people
to get more SD, or
check out the
extras.

Also check out the
source code.

Press A to continue.'''
LINES = MESSAGE.split('\n')


class IntroScreen(Runnable):
    def __init__(self, device_io: 'DeviceIO') -> None:
        self.device_io = device_io

        self.keep_running = True
        self.scroll = 0
        self.scroll_dir = 0

        self.view = BasicTextView(device_io.display)
        self.layout = SimpleLayout(device_io.display, self.view)

    def button_event(self, button, pressed):
        if button == 'a' and pressed and self.scroll == len(LINES) - self.view.max_line:
            self.keep_running = False

    def joystick_event(self, event, xy):
        if event == 'xy':
            if xy['y'] > 0.6:
                self.scroll_dir = 1
            elif xy['y'] < 0.4:
                self.scroll_dir = -1
            else:
                self.scroll_dir = 0
            self.display_lines()

    def display_lines(self):
        i = 0
        for i in range(min(self.view.max_line, len(LINES))):
            self.view.update(i, LINES[i + self.scroll])
            i += 1

    async def run(self):
        self.display_lines()

        self.device_io.buttons.subscribe(self.button_event, events=['a'])
        self.device_io.joystick.subscribe(self.joystick_event, events=['xy'])

        while self.keep_running:
            self.scroll = max(0, min(len(LINES) - self.view.max_line, self.scroll + self.scroll_dir))
            self.display_lines()
            self.layout.render()
            await asyncio.sleep(0.1)

        self.device_io.buttons.unsubscribe(self.button_event, events=['a'])
        self.device_io.joystick.unsubscribe(self.joystick_event, events=['xy'])
