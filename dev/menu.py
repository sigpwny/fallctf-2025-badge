import asyncio

from view import BasicTextView
from layout import ComplexLayout, Style


TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Callable
    from device_io import DeviceIO
    MenuItem = tuple[str, list['MenuItem'] | None, Callable[[], 'Runnable'] | None]


class Runnable:
    async def run(self):
        pass


class ListMenu(Runnable):
    def __init__(
        self,
        device_io: "DeviceIO",
        items: list['MenuItem'],
        *,
        additional_views=None,
    ):
        self.device_io = device_io
        self.sub_idx_ranges = []
        # cannot have 0 items
        items = items or [("no items", None, None)]
        self.actions: list[Callable[[], Runnable] | None] = []
        self.view = ComplexLayout(device_io.display)
        for name, sub, action in items:
            self.view.append(
                (
                    BasicTextView(device_io.display),
                    Style(posType=0b01, y=5),
                )
            )
            self.view[-1][0].update(0, "  " + name)
            self.actions.append(action)

            if sub is not None:
                st = len(self.view)
                for subname, _, action in sub:
                    # ignore submenu for submenus for now
                    self.view.append(
                        (
                            BasicTextView(device_io.display),
                            Style(posType=0b01, x=20, y=5, hidden=True),
                        )
                    )
                    self.view[-1][0].update(0, "  " + subname)
                    self.actions.append(action)
                self.sub_idx_ranges.append((st, len(self.view)))
        # init
        self.view[0][0].update(0, ">" + self.view[0][0].lines[0][1:])
        self.menu_end = len(self.view)
        if additional_views is not None:
            for v, s in additional_views:
                self.view.append((v, s))

        self.device_io.joystick.subscribe(self.joystick_event, events=["up-down"])
        self.device_io.buttons.subscribe(self.button_event, events=["a", "b"])
        self.view.first_render()

        self.keep_running = True
        self.a_pressed = False
        self.b_pressed = False
        self.last_select = 0
        self.select_idx = 0

    def joystick_event(self, event_type, value):
        if event_type == "up-down":
            if value:
                self.select_idx = (self.select_idx - 1) % self.menu_end
            else:
                self.select_idx = (self.select_idx + 1) % self.menu_end

    def button_event(self, button, pressed):
        self.a_pressed = button == "a" and pressed
        self.b_pressed = button == "b" and pressed

    async def run(self):
        while self.keep_running:
            viable_indices = [
                i for i, (_, s) in enumerate(self.view[: self.menu_end]) if not s.hidden
            ]
            self.select_idx = viable_indices[self.select_idx % len(viable_indices)]
            if self.b_pressed:
                for st, end in self.sub_idx_ranges:
                    if st <= self.select_idx < end:
                        # in a submenu
                        # toggle visibility of submenu
                        for i in range(st, end):
                            self.view[i][1].hidden = True
                        self.select_idx = st - 1
            if self.last_select != self.select_idx:
                self.view[self.last_select][0].update(
                    0, " " + self.view[self.last_select][0].lines[0][1:]
                )
                self.view[self.select_idx][0].update(
                    0, ">" + self.view[self.select_idx][0].lines[0][1:]
                )
                self.last_select = self.select_idx
            if self.a_pressed:
                if self.actions[self.select_idx] is not None:
                    self.keep_running = False
                    await self.actions[self.select_idx]().run()
                    continue
                for st, end in self.sub_idx_ranges:
                    if st == self.select_idx + 1:
                        # in a submenu
                        # toggle visibility of submenu
                        for i in range(st, end):
                            self.view[i][1].hidden = not self.view[i][1].hidden
                        self.view[self.select_idx][0].update(
                            0,
                            (">" if self.view[st][1].hidden else "V")
                            + self.view[self.select_idx][0].lines[0][1:],
                        )
            self.view.render()
            await asyncio.sleep(0.1)
