import asyncio
import esp32

from menu import Runnable, ListMenu, menu_with_text_runnable

from logger import log


def add_flag(persist, flag):
    past_flags = get_flags(persist)
    if flag in past_flags:
        return False
    past_flags.append(flag)
    combined = b'\x00'.join(f.encode('ascii') for f in past_flags)
    persist.set_blob('flags', combined)
    return True


def clear_flags(persist):
    persist.set_blob('flags', b'')


def get_flags(persist) -> list[str]:
    blob = persist.get_blob('flags')
    if blob is None or len(blob) == 0:
        return []
    return [f.decode('ascii') for f in blob.split(b'\x00') if f]


def get_installed_flags() -> list[str]:
    try:
        with open('flags.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except OSError:
        return []


def add_installed_flags(persist):
    for flag in get_installed_flags():
        added = add_flag(persist, flag)
        if added:
            log(f"Added installed flag: {flag}")


class FlagsMenu(Runnable):
    FLAG_WRAP_WIDTH = 19
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io
        self._go_back = False

    def _show_full_flag(self, flag):
        wrapped = [flag[i:i+self.FLAG_WRAP_WIDTH] for i in range(0, len(flag), self.FLAG_WRAP_WIDTH)]
        if flag in get_installed_flags():
            wrapped += ["(This flag cannot be", "removed)"]
        return menu_with_text_runnable(self.device_io, wrapped, [('OK', None, lambda: None)])

    def _clear_all_flags(self):
        def clear_flags_and_readd_installed():
            clear_flags(self.device_io.persist)
            add_installed_flags(self.device_io.persist)
        return menu_with_text_runnable(
            self.device_io,
            ["Are you sure you want", "to clear all flags?", "(This cannot be", "undone)"],
            [
                ('Cancel', None, lambda: None),
                ('Clear all', None, clear_flags_and_readd_installed)
            ]
        )

    async def run(self):
        menu = None
        while not self._go_back:
            flags = get_flags(self.device_io.persist)
            options = [
                ("back", None, lambda: setattr(self, '_go_back', True)),
                ("clear all flags", None, self._clear_all_flags())
            ] + [(f, None, self._show_full_flag(f)) for f in flags]
            last_selection_idx = 0 if menu is None else menu.select_idx
            if last_selection_idx >= len(options):
                last_selection_idx = len(options) - 1
            menu = ListMenu(self.device_io, options, init_selected=last_selection_idx)
            await menu.run()
