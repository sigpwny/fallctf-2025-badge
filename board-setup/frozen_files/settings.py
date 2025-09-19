import esp32

from menu import Runnable, ListMenu
from flag_manager import FlagsMenu

from invaders_game import InvadersGame

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class Persist:
    def __init__(self):
        self._nvs = esp32.NVS("fallctf_v1.0")
        self.boolean_settings = []

    def get_i32(self, key: str) -> int | None:
        try:
            return self._nvs.get_i32(key)
        except OSError:
            return None

    def set_i32(self, key: str, value: int, no_commit: bool = False):
        self._nvs.set_i32(key, value)
        if not no_commit:
            self._nvs.commit()

    def register_boolean_setting(self, name: str, default: bool):
        if name in self.boolean_settings:
            raise ValueError(f"Boolean setting '{name}' is already registered")
        self.boolean_settings.append(name)
        if self.get_i32(name) is None:
            self.set_i32(name, 1 if default else 0)

    def get_boolean(self, name: str) -> bool:
        if name not in self.boolean_settings:
            raise ValueError(f"Boolean setting '{name}' is not registered")
        value = self.get_i32(name)
        if value is None:
            raise ValueError(f"Boolean setting '{name}' is not set")
        return value != 0

    def set_boolean(self, name: str, value: bool):
        if name not in self.boolean_settings:
            raise ValueError(f"Boolean setting '{name}' is not registered")
        self.set_i32(name, 1 if value else 0)

    def toggle_boolean(self, name: str):
        if name not in self.boolean_settings:
            raise ValueError(f"Boolean setting '{name}' is not registered")
        current_value = self.get_boolean(name)
        self.set_boolean(name, not current_value)

    def set_blob(self, key: str, value: bytes):
        self._nvs.set_blob(key, value)
        self._nvs.commit()

    def get_blob(self, key: str) -> bytes | None:
        buf = bytearray(256)
        while len(buf) < 4096:  # limit to 4KB blobs
            try:
                length = self._nvs.get_blob(key, buf)
            except OSError as e:
                if len(e.args) > 1 and e.args[1] == "ESP_ERR_NVS_INVALID_LENGTH":
                    buf = bytearray(len(buf) * 2)
                else:
                    return None
            if length <= len(buf):
                break
        return bytes(buf[:length])


class SettingsMenu(Runnable):
    def __init__(self, device_io: "DeviceIO"):
        self.device_io = device_io
        self._go_back = False

    async def run(self):
        menu = None
        while not self._go_back:
            battery = self.device_io.power.get_battery_percentage()
            menu_options = [
                ("back", None, lambda: setattr(self, "_go_back", True)),
                ("Test speaker", None, lambda: self.device_io.speaker.success_sound()),
                (f"Battery: {battery}%", None, lambda: None),
                ("Flags", None, FlagsMenu(self.device_io)),
                ('Space Invaders', None, InvadersGame(self.device_io)),
            ]
            for setting in self.device_io.persist.boolean_settings:
                current_value = self.device_io.persist.get_boolean(setting)
                menu_options.append(
                    (
                        f"{setting}: {'ON' if current_value else 'OFF'}",
                        None,
                        lambda: self.device_io.persist.toggle_boolean(setting),
                    )
                )
            menu = ListMenu(
                self.device_io,
                menu_options,
                init_selected=0 if menu is None else menu.select_idx,
                exit_on_b_handler=lambda: setattr(self, "_go_back", True),
            )
            await menu.run()
