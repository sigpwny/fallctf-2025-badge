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


def clear_flags(persist):
    persist.set_blob('flags', b'')


def get_flags(persist) -> list[str]:
    blob = persist.get_blob('flags')
    if blob is None or len(blob) == 0:
        return []
    return [f.decode('ascii') for f in blob.split(b'\x00') if f]


class FlagsMenu(Runnable):
    FLAG_WRAP_WIDTH = 19
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io
        self._go_back = False

        add_flag(self.device_io.persist, "FLAG{EXAMPLE_FLAG_123456}")

    def _show_full_flag(self, flag):
        wrapped = [flag[i:i+self.FLAG_WRAP_WIDTH] for i in range(0, len(flag), self.FLAG_WRAP_WIDTH)]
        return menu_with_text_runnable(self.device_io, wrapped, [('OK', None, lambda: None)])

    async def run(self):
        flags = get_flags(self.device_io.persist)
        if not flags:
            await menu_with_text_runnable(self.device_io, ["No flags recorded."], [('OK', None, lambda: None)]).run()
            return

        menu = None
        while not self._go_back:
            options = [("back", None, lambda: setattr(self, '_go_back', True))] + [(f, None, self._show_full_flag(f)) for f in flags]
            menu = ListMenu(self.device_io, options, init_selected=0 if menu is None else menu.select_idx)
            await menu.run()
