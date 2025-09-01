from view import FontTextView
from logger import log
import time

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


def boot_screen(display, font_path="monospaceKrypton:24.mfnt", sleep=1):
    # type: (Display, str, int) -> None
    # TODO add logo view
    v = FontTextView(
        display=display, font_path=font_path, color=display.display.tft.GREEN, rot=45
    )
    v.update(20, 20, "SIGPWNY\n  2025  \n  FALLCTF")
    v.render()
    time.sleep(sleep)
