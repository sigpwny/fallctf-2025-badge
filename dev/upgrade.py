from menu import Runnable, menu_with_text
from ST7735 import TFTColor
from view import PBar, BasicTextView, BitMapView, UnboxedLine
from layout import Style, ComplexLayout
import asyncio


CATEGORIES = ["weapons", "shields", "thrusters", "sensors"]

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Literal
    from device_io import DeviceIO
    from menu import MenuItem

    SELECTING = Literal[0]
    ENTERING = Literal[1]
    ADJUSTING = Literal[2]
    CONFIRMING = Literal[3]
    CANCELLING = Literal[4]
else:
    SELECTING, ENTERING, ADJUSTING, CONFIRMING, CANCELLING = 0, 1, 2, 3, 4


class UpgradeMenu(Runnable):
    def __init__(self, device_io: "DeviceIO") -> None:
        self.device_io = device_io
        self.select_left = True
        self.select_bottom = True
        self.delta = 0
        self.state: "SELECTING | ENTERING | ADJUSTING | CONFIRMING | CANCELLING" = (
            SELECTING
        )

    def joystick_event(self, event_type, value):
        if self.state == SELECTING:
            if event_type == "up-down":
                self.select_bottom = not value
            else:
                # left-right
                self.select_left = value
        else:
            self.delta = (value * 2 - 1) if event_type == "left-right" else 0

    def button_event(self, button, pressed):
        if not pressed:
            return
        if button == "a":
            if self.state == SELECTING:
                # select it
                self.state = ENTERING
            else:
                # save
                self.state = CONFIRMING
        if button == "b":
            if self.state == SELECTING:
                self.keep_running = False
            else:
                self.state = CANCELLING

    async def run(self):
        with open("assets/shield_small.raw", "rb") as f:
            shield_img = bytearray(f.read())
        with open("assets/weapons_small.raw", "rb") as f:
            weapon_img = bytearray(f.read())
        with open("assets/thrusters_small.raw", "rb") as f:
            thruster_img = bytearray(f.read())
        with open("assets/sensors_small.raw", "rb") as f:
            sensor_img = bytearray(f.read())
        self.device_io.joystick.subscribe(
            self.joystick_event, events=["up-down", "left-right"]
        )
        self.device_io.buttons.subscribe(self.button_event, events=["a", "b"])
        # self.last_msg = ""
        self.keep_running = True
        # self.prev_stats = (self.device_io.ship_stats.stardust, self.device_io.ship_stats.stats.copy())
        # while self.keep_running:
        #     items: list[MenuItem] = []
        #     for s in ['weapons', 'shields', 'thrusters', 'sensors']:
        #         faction_buff = f' (+{self.device_io.ship_stats.faction.boosts[s]})' if s in self.device_io.ship_stats.faction.boosts else ''
        #         items.append((f'{s}: {self.device_io.ship_stats.stats[s]}{faction_buff}', None, self.upgrade_stat(s)))
        #     items.append(('confirm', None, self.confirm))
        #     items.append(('cancel', None, self.cancel))
        #     await menu_with_text(self.device_io, [f'StarDust: {self.device_io.ship_stats.stardust}', f'Cost: {self.device_io.ship_stats.cost_to_upgrade()}', self.last_msg], items, exit_on_b_handler=self.cancel)

        # maybe GUI?
        self.device_io.ship_stats.load()

        self.prev_select = 0
        # by python3 -c "from PIL import Image; import struct; img=Image.open('ship.png').convert('RGB'); open('ship.raw','wb').write(b''.join(struct.pack('>H',((r&0xF8)<<8)|((g&0xFC)<<3)|(b>>3)) for y in range(img.height) for x in range(img.width) for r,g,b in [img.getpixel((x,y))]))"
        with open("assets/ship.raw", "rb") as f:
            ship_img = bytearray(f.read())

        start_idx = 13
        inputs_idx = [start_idx, start_idx + 1, start_idx + 3, start_idx + 4]
        start_idx = 5
        value_text_idx = [start_idx + 1, start_idx + 3, start_idx + 5, start_idx + 7]
        line_colors = [
            self.device_io.display.display.tft.RED,
            self.device_io.display.display.tft.BLUE,
            TFTColor(0xFF, 0xA5, 0x00),  # orange
            self.device_io.display.display.tft.GREEN,
        ]

        l = ComplexLayout(
            self.device_io.display,
            (
                BasicTextView(self.device_io.display),
                Style(),
            ),
            # fmt: off
            (
                UnboxedLine(self.device_io.display, 5 + 28 + 2, 20 + 10 + 2, 52 - 2, 40 - 2, self.device_io.display.display.tft.BLACK),
                Style(posType=0b00, x=0, y=0),
            ),
            (
                UnboxedLine(self.device_io.display, 100 - 2, 20 + 10 + 2, 52 + 34 + 2, 40 - 2, self.device_io.display.display.tft.BLACK),
                Style(posType=0b00, x=0, y=0),
            ),
            (
                UnboxedLine(self.device_io.display, 5 + 28 + 2, 90 - 2, 52 - 2, 40 + 42 + 2, self.device_io.display.display.tft.BLACK),
                Style(posType=0b00, x=0, y=0),
            ),
            (
                UnboxedLine(self.device_io.display, 100 - 2, 90 - 2, 52 + 34 + 2, 40 + 42 + 2, self.device_io.display.display.tft.BLACK),
                Style(posType=0b00, x=0, y=0),
            ),
            (
                BitMapView(self.device_io.display, weapon_img, 23, 20, format=1),
                Style(posType=0b00, x=5, y=35),
            ),
            (
                BasicTextView(self.device_io.display, lines=[str(self.device_io.ship_stats.faction.boosts[CATEGORIES[0]] + self.device_io.ship_stats.stats[CATEGORIES[0]])]),
                Style(posType=0b10, x=5, y=35)
            ),
            (
                BitMapView(self.device_io.display, shield_img, 17, 20, format=1),
                Style(posType=0b00, x=105, y=35),
            ),
            (
                BasicTextView(self.device_io.display, lines=[str(self.device_io.ship_stats.faction.boosts[CATEGORIES[1]] + self.device_io.ship_stats.stats[CATEGORIES[1]])]),
                Style(posType=0b10, x=5, y=35)
            ),
            (
                BitMapView(self.device_io.display, thruster_img, 16, 20, format=1),
                Style(posType=0b00, x=5, y=105),
            ),
            (
                BasicTextView(self.device_io.display, lines=[str(self.device_io.ship_stats.faction.boosts[CATEGORIES[2]] + self.device_io.ship_stats.stats[CATEGORIES[2]])]),
                Style(posType=0b10, x=5, y=105)
            ),
            (
                BitMapView(self.device_io.display, sensor_img, 19, 19, format=1),
                Style(posType=0b00, x=105, y=105),
            ),
            (
                BasicTextView(self.device_io.display, lines=[str(self.device_io.ship_stats.faction.boosts[CATEGORIES[3]] + self.device_io.ship_stats.stats[CATEGORIES[3]])]),
                Style(posType=0b10, x=5, y=105)
            ),
            # fmt: on
            (
                PBar(
                    self.device_io.display,
                    50,
                    self.device_io.ship_stats.stats[CATEGORIES[0]],
                    width=28,
                    text_mode=2,
                    fg_color=self.device_io.display.display.tft.YELLOW,  # default selection
                ),
                Style(posType=0b00, x=5, y=20),
            ),
            (
                PBar(
                    self.device_io.display,
                    50,
                    self.device_io.ship_stats.stats[CATEGORIES[1]],
                    width=28,
                    text_mode=2,
                ),
                Style(posType=0b00, x=100, y=20),
            ),
            (
                BitMapView(self.device_io.display, ship_img, 34, 42, format=1),
                Style(posType=0b00, x=50, y=40),
            ),
            (
                PBar(
                    self.device_io.display,
                    50,
                    self.device_io.ship_stats.stats[CATEGORIES[2]],
                    width=28,
                    text_mode=2,
                ),
                Style(posType=0b00, x=5, y=90),
            ),
            (
                PBar(
                    self.device_io.display,
                    50,
                    self.device_io.ship_stats.stats[CATEGORIES[3]],
                    width=28,
                    text_mode=2,
                ),
                Style(posType=0b00, x=100, y=90),
            ),
            enable_render_cache=True,
        )

        def text_updater(pts):
            l[0][0].update(0, f"StarDust: {self.device_io.ship_stats.stardust}")
            l[0][0].update(1, f"Cost: {self.device_io.ship_stats.cost_to_upgrade(pts)}")

        text_updater(0)

        prev_val = 0

        while self.keep_running:
            curr_select = self.select_left + 2 * self.select_bottom
            curr: "PBar" = l[inputs_idx[curr_select]][0]
            if self.state == SELECTING:
                if curr_select != self.prev_select:
                    curr.set_color(self.device_io.display.display.tft.YELLOW)
                    l[1 + curr_select][0].set_color(line_colors[curr_select])
                    l[inputs_idx[self.prev_select]][0].set_color(
                        self.device_io.display.display.tft.WHITE
                    )
                    l[1 + self.prev_select][0].set_color(
                        self.device_io.display.display.tft.BLACK
                    )
                    self.prev_select = curr_select
            elif self.state == CONFIRMING:
                self.delta = 0
                if not self.device_io.ship_stats.upgrade(
                    CATEGORIES[self.select_left + 2 * self.select_bottom],
                    pts_delta=curr.value - prev_val,
                ):
                    l[0][0].shake()
                    self.state = ADJUSTING
                else:
                    text_updater(0)
                    l[value_text_idx[curr_select]][0].update(
                        0,
                        str(
                            self.device_io.ship_stats.faction.boosts[
                                CATEGORIES[curr_select]
                            ]
                            + curr.value
                        ),
                    )
                    curr.update(curr.value, initial_value=curr.value)
                    curr.set_color(self.device_io.display.display.tft.YELLOW)
                    self.prev_select = self.select_left + 2 * self.select_bottom
                    self.state = SELECTING
            elif self.state == ENTERING:
                curr.set_color(self.device_io.display.display.tft.GREEN)
                prev_val = curr.value
                self.state = ADJUSTING
            elif self.state == CANCELLING:
                self.delta = 0
                text_updater(0)
                curr.update(prev_val)
                curr.set_color(self.device_io.display.display.tft.YELLOW)
                self.prev_select = self.select_left + 2 * self.select_bottom
                self.state = SELECTING
            elif self.delta != 0:
                if curr.update(curr.value + self.delta) != 0:
                    curr.shake()
                else:
                    text_updater(curr.value - prev_val)
            l.render()
            await asyncio.sleep(0.1)

    # def confirm(self):
    #     self.keep_running = False

    # def cancel(self):
    #     self.device_io.ship_stats.stardust, self.device_io.ship_stats.stats = (
    #         self.prev_stats
    #     )
    #     self.keep_running = False

    # def undo(self):
    #     if self.prev_stats is not None:
    #         self.device_io.ship_stats.save()
    #         self.last_msg = "Undid upgrade"
    #     self.prev_stats = None

    # def upgrade_stat(self, stat: str):
    #     def upgrade_stat():
    #         if self.device_io.ship_stats.upgrade(stat):
    #             self.last_msg = f"Upgraded {stat}"
    #         else:
    #             self.last_msg = "Not enough SD"

    #     return upgrade_stat
