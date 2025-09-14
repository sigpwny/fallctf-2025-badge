from machine import Pin, PWM
import asyncio
from logger import log

class PWMSpeaker:
    def __init__(self):
        """Initialize the speaker with the given pin number."""

        self.BUZZVOL_PIN = 3
        self.BUZZ_PIN = 9
        self.pwm = PWM(Pin(self.BUZZ_PIN))
        self.pwm.duty_u16(0)
        self.is_playing = False

        Pin(self.BUZZVOL_PIN, Pin.OUT).off() # ground the other pin of the buzzer

    def play_tone(self, frequency, duty=512):
        """Play a tone at the given frequency (Hz) and duty cycle (0-1023)."""  
        if self.is_playing:   
            return
        self.pwm.freq(frequency)
        self.pwm.duty(duty)
        self.is_playing = True

    def stop(self):
        """Stop playing any sound."""
        self.pwm.duty_u16(0)
        self.is_playing = False
        

class Speaker:
    def __init__(self):
        self.speaker = PWMSpeaker()
    
    def beep(self, frequency=1000, duration_ms=100):
        """Non-blocking version of beep that returns immediately"""
        log(f"Beep (nowait): {frequency}Hz for {duration_ms}ms")
        self.speaker.play_tone(frequency)
        async def stop_later():
            await asyncio.sleep_ms(duration_ms)
            self.speaker.stop()
        asyncio.create_task(stop_later())
    
    def success_sound(self):
        """Play a non-blocking success sound (ascending tones)"""
        log("Playing success sound")
        frequencies = [1000, 1200, 1500]  # ascending frequencies
        duration_ms = 80  # duration for each tone
        
        async def play_sequence():
            for i, freq in enumerate(frequencies):
                # Add delay between tones except for the first one
                if i > 0:
                    await asyncio.sleep_ms(20)  # 20ms delay
                self.speaker.play_tone(freq)
                await asyncio.sleep_ms(duration_ms)
                self.speaker.stop()
        
        asyncio.create_task(play_sequence())
    
    async def run(self):
        pass