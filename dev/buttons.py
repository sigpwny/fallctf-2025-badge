import asyncio
from logger import log
from machine import Pin


class Buttons:
    def __init__(self):
        self.subscribers = {'a': [], 'b': []}
        self.btn_a_pin = 13
        self.btn_b_pin = 0
        self._btn_a = Pin(self.btn_a_pin, Pin.IN)
        self._btn_b = Pin(self.btn_b_pin, Pin.IN)

    def subscribe(self, callback, events):
        """
        Subscribe to button events.
        :param callback: function to call on event
        :param events: event types to subscribe to ('a', 'b')
        """
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].append(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    async def run(self):
        # buttons are active low
        prev_a_state = self._btn_a.value()
        prev_b_state = self._btn_b.value()

        while True:
            a_state = self._btn_a.value()
            b_state = self._btn_b.value()

            if a_state != prev_a_state:
                for callback in self.subscribers['a']:
                    callback('a', a_state == 0)
                prev_a_state = a_state
            if b_state != prev_b_state:
                for callback in self.subscribers['b']:
                    callback('b', b_state == 0)
                prev_b_state = b_state
            await asyncio.sleep_ms(1)
