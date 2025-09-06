from machine import ADC, Pin


class PowerMonitor:
    """
    Monitors power consumption and battery voltage.
    """

    ISENSE_ADC_PIN = 10
    ISENSE_GAIN = 50
    ISENSE_RESISTOR = 0.1  # Ohm
    MAIN_VOLTAGE = 3.3  # Volts

    BATTERY_VOLTAGE_DIVIDER_RATIO = 2  # 100k and 100k voltage divider
    CHARGE_ADC_PIN = 8  # ADC pin for battery voltage measurement

    BATTERY_FULL_VOLTAGE = 4.1  # Volts
    BATTERY_5_PERCENT_VOLTAGE = 3.5  # Volts

    def __init__(self):
        self.current_adc = ADC(Pin(self.ISENSE_ADC_PIN))
        self.current_adc.atten(ADC.ATTN_0DB)
        self.charge_adc = ADC(Pin(self.CHARGE_ADC_PIN))
        self.charge_adc.atten(ADC.ATTN_11DB)

    def read_current(self):
        """
        Reads the current consumption in milliamps.
        """
        isense_voltage = self.current_adc.read_uv() / 1e6
        current_a = isense_voltage / (self.ISENSE_RESISTOR * self.ISENSE_GAIN)
        current_ma = current_a * 1000
        return current_ma

    def read_battery_voltage(self):
        """
        Reads the battery voltage in volts.
        """
        charge_voltage = self.charge_adc.read_uv() / 1e6
        battery_voltage = charge_voltage * self.BATTERY_VOLTAGE_DIVIDER_RATIO
        return battery_voltage

    def get_power_draw(self, n=10):
        """
        Returns the current power draw in milliwatts.
        """
        total_current_ma = 0
        for _ in range(n):
            total_current_ma += self.read_current()
        current_ma = total_current_ma / n
        power_mw = current_ma * self.MAIN_VOLTAGE
        return power_mw

    def get_battery_percentage(self):
        """
        Estimates the battery percentage based on voltage.
        """
        voltage = self.read_battery_voltage()
        if voltage >= self.BATTERY_FULL_VOLTAGE:
            return 100
        elif voltage < self.BATTERY_5_PERCENT_VOLTAGE:
            return 1
        else:
            percentage = 5.0 + (voltage - self.BATTERY_5_PERCENT_VOLTAGE) / (self.BATTERY_FULL_VOLTAGE - self.BATTERY_5_PERCENT_VOLTAGE) * 95.0
            return int(percentage)

    async def run(self):
        pass
