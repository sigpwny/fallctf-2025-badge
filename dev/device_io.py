TYPE_CHECKING = False
if TYPE_CHECKING:
    from joystick import Joystick
    from buttons import Buttons
    from display import Display
    from soft_display import SoftDisplay
    from ship_stats import ShipStats
    from accelerometer import Accelerometer


class DeviceIO:
    def __init__(self, joystick: 'Joystick', buttons: 'Buttons', accelerometer: 'Accelerometer', display: 'Display | SoftDisplay', ship_stats: 'ShipStats'):
        self.joystick = joystick
        self.buttons = buttons
        self.display = display
        self.ship_stats = ship_stats
        self.accelerometer = accelerometer
