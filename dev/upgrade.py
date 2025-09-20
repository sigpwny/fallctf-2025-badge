from menu import Runnable, menu_with_text
from view import PBar, BasicTextView, BitMapView
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
                if value:
                    self.select_bottom = False
                else:
                    self.select_bottom = True
            elif event_type == "left-right":
                if value:
                    self.select_left = True
                else:
                    self.select_left = False
        else:
            if event_type == "left-right":
                if value:
                    self.delta = 1
                else:
                    self.delta = -1
            else:
                self.delta = 0

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
        # TODO tmp fix
        for s in CATEGORIES:
            if s not in self.device_io.ship_stats.faction.boosts:
                self.device_io.ship_stats.faction.boosts[s] = 0

        self.prev_select = (self.select_left, self.select_bottom)
        # by python3 -c "from PIL import Image; import struct; img=Image.open('ship.png').convert('RGB'); open('ship.raw','wb').write(b''.join(struct.pack('>H',((r&0xF8)<<8)|((g&0xFC)<<3)|(b>>3)) for y in range(img.height) for x in range(img.width) for r,g,b in [img.getpixel((x,y))]))"
        with open("assets/ship.raw", "rb") as f:
            ship_img = bytearray(f.read())

        l = ComplexLayout(
            self.device_io.display,
            (
                BasicTextView(self.device_io.display),
                Style(),
            ),
            (
                PBar(
                    self.device_io.display,
                    100,
                    self.device_io.ship_stats.faction.boosts[CATEGORIES[0]],
                    width=30,
                    text_mode=2,
                ),
                Style(posType=0b01, x=10, y=5),
            ),
            (
                PBar(
                    self.device_io.display,
                    100,
                    self.device_io.ship_stats.faction.boosts[CATEGORIES[1]],
                    width=30,
                    text_mode=2,
                ),
                Style(posType=0b11, x=40),
            ),
            (
                BitMapView(self.device_io.display, ship_img, 34, 42, format=1),
                Style(posType=0b01, x=60, y=-10),
            ),
            (
                PBar(
                    self.device_io.display,
                    100,
                    self.device_io.ship_stats.faction.boosts[CATEGORIES[2]],
                    width=30,
                    text_mode=2,
                ),
                Style(posType=0b01, x=10),
            ),
            (
                PBar(
                    self.device_io.display,
                    100,
                    self.device_io.ship_stats.faction.boosts[CATEGORIES[3]],
                    width=30,
                    text_mode=2,
                ),
                Style(posType=0b11, x=40),
            ),
        )

        def text_updater():
            l[0][0].update(0, f"StarDust: {self.device_io.ship_stats.stardust}")
            l[0][0].update(1, f"Cost: {self.device_io.ship_stats.cost_to_upgrade()}")

        text_updater()

        prev_val = 0

        while self.keep_running:
            curr_select = (self.select_left, self.select_bottom)
            curr: "PBar" = l[1 + self.select_left + 3 * self.select_bottom][0]
            if self.state == SELECTING:
                if curr_select != self.prev_select:
                    curr.set_color(self.device_io.display.display.tft.YELLOW)
                    l[1 + self.prev_select[0] + 3 * self.prev_select[1]][0].set_color(
                        self.device_io.display.display.tft.WHITE
                    )
                    self.prev_select = curr_select
            elif self.state == CONFIRMING:
                # TODO: confirm
                self.delta = 0
                curr.set_color(self.device_io.display.display.tft.YELLOW)
                self.prev_select = (self.select_left, self.select_bottom)
                self.state = SELECTING
            elif self.state == ENTERING:
                curr.set_color(self.device_io.display.display.tft.GREEN)
                prev_val = curr.value
                self.state = ADJUSTING
            elif self.state == CANCELLING:
                self.delta = 0
                curr.update(prev_val)
                curr.set_color(self.device_io.display.display.tft.YELLOW)
                self.prev_select = (self.select_left, self.select_bottom)
                self.state = SELECTING
            elif self.delta != 0:
                # TODO: do upgrade
                if curr.update(curr.value + self.delta) != 0:
                    curr.shake()
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
