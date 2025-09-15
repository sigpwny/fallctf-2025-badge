import asyncio

from view import BasicTextView
from layout import ComplexLayout, Style


TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Callable
    from device_io import DeviceIO
    MenuItem = tuple[str, list['MenuItem'] | None, 'Runnable' | Callable[[], 'Runnable | None'] | None]


class Runnable:
    async def run(self):
        pass


class ListMenu(Runnable):
    def __init__(
        self,
        device_io: "DeviceIO",
        items: list['MenuItem'],
        init_selected: int = 0,
        *,
        additional_views=None,
        prepended_views=None,
        cancel_event=None
    ):
        self.device_io = device_io
        self.sub_idx_ranges = []
        # cannot have 0 items
        items = items or [("no items", None, None)]
        self.actions: list[Callable[[], Runnable] | None] = []
        self.view = ComplexLayout(device_io.display)
        if prepended_views is not None:
            for v, s in prepended_views:
                self.view.append((v, s))
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
        self.menu_start = len(prepended_views) if prepended_views else 0
        self.menu_end = len(self.view)

        if additional_views is not None:
            for v, s in additional_views:
                self.view.append((v, s))

        self.device_io.joystick.subscribe(self.joystick_event, events=["up-down"])
        self.device_io.buttons.subscribe(self.button_event, events=["a", "b"])
        self.view.first_render()

        self.keep_running = True
        self.item_selected = False
        self.last_select = init_selected + self.menu_start
        self.select_idx = init_selected + self.menu_start
        self._wrap_select_idx()

        first_selected_view = self.view[self.select_idx][0]
        first_selected_view.update(0, ">" + first_selected_view.lines[0][1:])

        self.cancel_event = cancel_event

    def _wrap_select_idx(self):
        self.select_idx = (self.select_idx - self.menu_start) % (self.menu_end - self.menu_start) + self.menu_start

    def joystick_event(self, event_type, value):
        if event_type == "up-down":
            if value:
                self.select_idx -= 1
            else:
                self.select_idx += 1
            self._wrap_select_idx()


    def button_event(self, button, pressed):
        if not pressed:
            return
        if button == 'a':
            if self.actions[self.select_idx - self.menu_start] is not None:
                self.keep_running = False
                self.item_selected = True
                return
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
        elif button == 'b':
            for st, end in self.sub_idx_ranges:
                if st <= self.select_idx < end:
                    # in a submenu
                    # toggle visibility of submenu
                    for i in range(st, end):
                        self.view[i][1].hidden = True
                    self.select_idx = st - 1
                    return
            self.keep_running = False

    async def run(self):
        while self.keep_running:
            if self.last_select != self.select_idx:
                self.view[self.last_select][0].update(
                    0, " " + self.view[self.last_select][0].lines[0][1:]
                )
                self.view[self.select_idx][0].update(
                    0, ">" + self.view[self.select_idx][0].lines[0][1:]
                )
                self.last_select = self.select_idx
            self.view.render()
            await asyncio.sleep_ms(20)
            if self.cancel_event is not None and self.cancel_event.is_set():
                self.keep_running = False
        if self.item_selected:
            action = self.actions[self.select_idx - self.menu_start]
            if action is not None:
                if isinstance(action, Runnable):
                    await action.run()
                elif callable(action):
                    result = action()
                    # await if it's a coroutine
                    if hasattr(result, '__await__'):
                        await result
                else:
                    raise ValueError("Action is neither Runnable nor callable")

        self.device_io.joystick.unsubscribe(self.joystick_event, events=["up-down"])
        self.device_io.buttons.unsubscribe(self.button_event, events=["a", "b"])

class ImageMenu(Runnable):
    def __init__(self, device_io: 'DeviceIO', image_paths, actions):
        self.device_io = device_io
        self.image_paths = image_paths
        self.actions = actions
        self.select_idx = 0
        self.keep_running = True

    def joystick_event(self, event_type, value):
        if event_type == "up-down":
            if value:
                self.select_idx -= 1
            else:
                self.select_idx += 1
            self.select_idx = self.select_idx % len(self.image_paths)
            self.device_io.display.draw_fullscreen_image(self.image_paths[self.select_idx])
            self.device_io.display.show()

    def button_event(self, button, pressed):
        if not pressed:
            return
        if button == 'a':
            self.keep_running = False

    async def run(self):
        self.device_io.joystick.subscribe(self.joystick_event, events=["up-down"])
        self.device_io.buttons.subscribe(self.button_event, events=["a"])

        self.device_io.display.draw_fullscreen_image(self.image_paths[self.select_idx])
        self.device_io.display.show()

        while self.keep_running:
            await asyncio.sleep_ms(10)

        self.device_io.joystick.unsubscribe(self.joystick_event, events=["up-down"])
        self.device_io.buttons.unsubscribe(self.button_event, events=["a"])

        action = self.actions[self.select_idx]
        if action is not None:
            if isinstance(action, Runnable):
                await action.run()
            elif callable(action):
                result = action()
                # await if it's a coroutine
                if hasattr(result, '__await__'):
                    await result
            else:
                raise ValueError("Action is neither Runnable nor callable")


async def menu_with_text(device_io: 'DeviceIO', text_list: list[str], menu_items: list['MenuItem'], cancel_event=None):
    text_view = BasicTextView(device_io.display)
    for i, line in enumerate(text_list):
        text_view.update(i, line)
    await ListMenu(
        device_io,
        menu_items,
        prepended_views=[(text_view, Style(posType=0b01, y=5))], # relative y with 5px top margin
        cancel_event=cancel_event
    ).run()
