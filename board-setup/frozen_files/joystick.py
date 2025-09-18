import asyncio
from logger import log
from machine import ADC, Pin


class Joystick:
    def __init__(self):
        self.subscribers = {'xy': [], 'up-down': [], 'left-right': []}
        self._x_pin = 5
        self._y_pin = 4
        self._calibration_x_center = 0.815
        self._calibration_x_max = 1.4
        self._calibration_y_center = 0.808
        self._calibration_y_max = 1.43

    def subscribe(self, callback, events):
        """
        Subscribe to joystick events.
        :param callback: function to call on event
        :param events: event types to subscribe to ('xy': any movement, 'up-down': True for down, 'left-right': True for right)
        """
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].append(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    def unsubscribe(self, callback, events):
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].remove(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    def _current_val(self):
        pass

    async def run(self):
        x_adc = ADC(Pin(self._x_pin))
        x_adc.atten(ADC.ATTN_11DB)
        y_adc = ADC(Pin(self._y_pin))
        y_adc.atten(ADC.ATTN_11DB)

        # the joystick values are oriented such that (0, 0) is the top-right corner

        # these thresholds are relative to halfway point
        on_threshold = 0.3
        off_threshold = 0.1

        x_dir_state = 0  # -1: right, 0: neutral, 1: left
        y_dir_state = 0  # -1: up, 0: neutral, 1: down
        prev_x_dir_state = 0
        prev_y_dir_state = 0

        while True:
            x_raw = x_adc.read_uv() / 1e6
            y_raw = y_adc.read_uv() / 1e6
            x_val = 0.5 + (x_raw - self._calibration_x_center) / (self._calibration_x_max - self._calibration_x_center) / 2
            y_val = 0.5 + (y_raw - self._calibration_y_center) / (self._calibration_y_max - self._calibration_y_center) / 2
            # clamp to [0, 1]
            x_val = max(0.0, min(1.0, x_val))
            y_val = max(0.0, min(1.0, y_val))

            for callback in self.subscribers['xy']:
                callback('xy', {'x': x_val, 'y': y_val})

            if abs(x_val - 0.5) < off_threshold:
                x_dir_state = 0
            elif x_val > 0.5 + on_threshold:
                x_dir_state = 1
            elif x_val < 0.5 - on_threshold:
                x_dir_state = -1
            if abs(y_val - 0.5) < off_threshold:
                y_dir_state = 0
            elif y_val > 0.5 + on_threshold:
                y_dir_state = 1
            elif y_val < 0.5 - on_threshold:
                y_dir_state = -1

            if x_dir_state != prev_x_dir_state and x_dir_state != 0:
                for callback in self.subscribers['left-right']:
                    callback('left-right', x_dir_state == -1)
            prev_x_dir_state = x_dir_state
            if y_dir_state != prev_y_dir_state and y_dir_state != 0:
                for callback in self.subscribers['up-down']:
                    callback('up-down', y_dir_state == -1)
            prev_y_dir_state = y_dir_state

            await asyncio.sleep_ms(10)
