from view import FontTextView
from logger import log
import time

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


def boot_screen(display: "Display", font_path="monospaceKrypton_font", sleep=5):
    # TODO add logo view
    v = FontTextView(
        display=display,
        font_path=font_path,
        fgcolor=display.display.tft.GREEN,
    )
    v.update(10, 20, "SIGPWNY\n  2025  \n  FALLCTF")
    v.render()
    time.sleep(sleep)
