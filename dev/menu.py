import asyncio
import framebuf

from microfont import MicroFont
from view import BasicTextView
from layout import ComplexLayout, Style
from logger import log


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
        cancel_event=None,
        exit_on_b_handler=None,
        enable_render_cache=False,
    ):
        self.device_io = device_io
        self.sub_idx_ranges = []
        # cannot have 0 items
        items = items or [("no items", None, None)]
        self.actions: list[Callable[[], Runnable] | None] = []
        self.view = ComplexLayout(device_io.display, enable_render_cache=enable_render_cache)
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

        self.keep_running = True
        self.item_selected = False
        self.last_select = init_selected + self.menu_start
        self.select_idx = init_selected + self.menu_start
        self._wrap_select_idx()

        first_selected_view = self.view[self.select_idx][0]
        first_selected_view.update(0, ">" + first_selected_view.lines[0][1:])

        self.cancel_event = cancel_event
        self.exit_on_b_handler = exit_on_b_handler
        self.controls_on = True

    def _wrap_select_idx(self):
        self.select_idx = (self.select_idx - self.menu_start) % (self.menu_end - self.menu_start) + self.menu_start

    def joystick_event(self, event_type, value):
        if not self.controls_on:
            return
        if event_type == "up-down":
            if value:
                self.select_idx -= 1
            else:
                self.select_idx += 1
            self._wrap_select_idx()


    def button_event(self, button, pressed):
        if not pressed or not self.controls_on:
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
            if self.exit_on_b_handler is not None:
                self.keep_running = False
                self.exit_on_b_handler()

    async def run(self):
        self.device_io.joystick.subscribe(self.joystick_event, events=["up-down"])
        self.device_io.buttons.subscribe(self.button_event, events=["a", "b"])
        self.view.first_render()

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
                self.controls_on = False
                if isinstance(action, Runnable):
                    await action.run()
                elif callable(action):
                    result = action()
                    # await if it's a coroutine
                    if hasattr(result, '__await__'):
                        await result
                elif hasattr(action, '__await__'):
                    await action
                else:
                    raise ValueError("Action is neither Runnable nor callable nor awaitable")
                self.controls_on = True

        self.device_io.joystick.unsubscribe(self.joystick_event, events=["up-down"])
        self.device_io.buttons.unsubscribe(self.button_event, events=["a", "b"])

class HomeMenu(Runnable):
    NUM_ITEMS = 4
    MAX_IMAGES_SIZE = 40 * 27 * 2  # width * height * bytes_per_pixel (RGB565)

    def __init__(self, device_io: 'DeviceIO', actions):
        self.device_io = device_io
        if len(actions) != self.NUM_ITEMS:
            raise ValueError(f"actions must have exactly {self.NUM_ITEMS} items")
        self.actions = actions
        self.select_idx = 0
        self.last_select_idx = 0
        self.keep_running = True
        self.labels = ['CONNECT', 'UPGRADE', 'MORE', 'SETTINGS']
        planets = ['sun', 'earth', 'moon', 'uranus']
        self.big_planet_paths = [f'assets/{p}_big.raw' for p in planets]
        self.small_planet_paths = [f'assets/{p}_small.raw' for p in planets]

        self.small_font = MicroFont('assets/comic_sans:B:14.mfnt', cache_index=True, cache_chars=True)
        self.large_font = MicroFont('assets/comic_sans:B:16.mfnt', cache_index=True, cache_chars=True)

    def joystick_event(self, event_type, value):
        if event_type == "up-down":
            self.last_select_idx = self.select_idx
            if value:
                self.select_idx -= 1
            else:
                self.select_idx += 1
            self.select_idx = self.select_idx % self.NUM_ITEMS
            self.draw()

    def button_event(self, button, pressed):
        if not pressed:
            return
        if button == 'a':
            self.keep_running = False

    def draw_text(self, x, y, text, large_font=False):
        font = self.large_font if large_font else self.small_font
        font.write(
            text,
            self.device_io.display.display.buffer,
            framebuf.RGB565,
            self.device_io.display.display.width,
            self.device_io.display.display.height,
            x,
            y,
            self.device_io.display.display.tft.WHITE,
            y_spacing=0,
            x_spacing=0,
        )

    def draw_initial(self):
        global global_buffer

        self.device_io.display.clear()
        for i in range(self.NUM_ITEMS):
            if i == self.select_idx:
                path = self.big_planet_paths[i]
                if 'uranus' in path:
                    width, height = 40, 27
                else:
                    width, height = 27, 27
            else:
                path = self.small_planet_paths[i]
                if 'uranus' in path:
                    width, height = 28, 17
                else:
                    width, height = 17, 17
            x = (27 - width) // 2 + 15
            y = 5 + i * 30 + (27 - height) // 2
            with open(path, 'rb') as f:
                length = f.readinto(global_buffer)
                bitmap = (global_buffer, width, height, framebuf.RGB565)
                self.device_io.display.display.blit(bitmap, x, y, 0)

        for i in range(self.NUM_ITEMS):
            self.draw_text(50, 12 + i * 30, self.labels[i], large_font=(i == self.select_idx))
        self.device_io.display.show()

    def draw(self):
        global global_buffer

        # draw new big planet
        path = self.big_planet_paths[self.select_idx]
        if 'uranus' in path:
            width, height = 40, 27
        else:
            width, height = 27, 27
        x = (27 - width) // 2 + 15
        y = 5 + self.select_idx * 30 + (27 - height) // 2
        self.device_io.display.display.rect(x, y, width, height, 0, True)
        with open(path, 'rb') as f:
            length = f.readinto(global_buffer)
            bitmap = (global_buffer, width, height, framebuf.RGB565)
            self.device_io.display.display.blit(bitmap, x, y, 0)

        # draw new big text
        self.device_io.display.display.rect(50, 12 + self.select_idx * 30, 100, 30, 0, True)
        self.draw_text(50, 12 + self.select_idx * 30, self.labels[self.select_idx], large_font=True)

        # draw small planet
        path = self.small_planet_paths[self.last_select_idx]
        if 'uranus' in path:
            width, height = 28, 17
        else:
            width, height = 17, 17
        x = (27 - 40) // 2 + 15
        y = 5 + self.last_select_idx * 30 + (27 - 27) // 2
        self.device_io.display.display.rect(x, y, 40, 27, 0, True)
        x = (27 - width) // 2 + 15
        y = 5 + self.last_select_idx * 30 + (27 - height) // 2
        with open(path, 'rb') as f:
            length = f.readinto(global_buffer)
            bitmap = (global_buffer, width, height, framebuf.RGB565)
            self.device_io.display.display.blit(bitmap, x, y, 0)

        # draw new big text
        self.device_io.display.display.rect(50, 12 + self.last_select_idx * 30, 100, 30, 0, True)
        self.draw_text(50, 12 + self.last_select_idx * 30, self.labels[self.last_select_idx], large_font=False)

        self.device_io.display.show()


    async def run(self):
        self.device_io.joystick.subscribe(self.joystick_event, events=["up-down"])
        self.device_io.buttons.subscribe(self.button_event, events=["a"])

        self.draw_initial()

        while self.keep_running:
            await asyncio.sleep_ms(100)

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
            elif hasattr(action, '__await__'):
                await action
            else:
                raise ValueError("Action is neither Runnable nor callable nor awaitable")


global_buffer = bytearray(HomeMenu.MAX_IMAGES_SIZE)


async def menu_with_text(device_io: 'DeviceIO', text_list: list[str], menu_items: list['MenuItem'], cancel_event=None, exit_on_b_handler=None):
    text_view = BasicTextView(device_io.display)
    for i, line in enumerate(text_list):
        text_view.update(i, line)
    await ListMenu(
        device_io,
        menu_items,
        prepended_views=[(text_view, Style(posType=0b01, y=5))], # relative y with 5px top margin
        cancel_event=cancel_event,
        exit_on_b_handler=exit_on_b_handler
    ).run()


def menu_with_text_runnable(device_io: 'DeviceIO', text_list: list[str], menu_items: list['MenuItem'], cancel_event=None):
    text_view = BasicTextView(device_io.display)
    for i, line in enumerate(text_list):
        text_view.update(i, line)
    return ListMenu(
        device_io,
        menu_items,
        prepended_views=[(text_view, Style(posType=0b01, y=5))], # relative y with 5px top margin
        cancel_event=cancel_event
    )
