from view import FontTextView
from logger import log
import time


def boot_screen(display, font_path="monospaceKrypton_font", sleep=5):
    # TODO add logo view
    v = FontTextView(
        display=display,
        font_path=font_path,
        fgcolor=display.display.tft.GREEN,
        bgcolor=display.display.tft.WHITE,
    )
    v.update(10, 20, "SIGPWNY\n  2025  \n  FALLCTF")
    v.render()
    time.sleep(sleep)
