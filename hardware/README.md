# Hardware

I recommend using Github's outline feature to navigate this document.

## Microcontroller

The badge has an ESP32-S2-SOLO-2-N4 module. This module features an ESP32-S2 SoC with 4MB of flash and internal antenna for 2.4Ghz Wi-Fi (no bluetooth).

The datasheet for the ESP32-S2-SOLO-2-N4 module is available [here](https://www.espressif.com/sites/default/files/documentation/esp32-s2-solo-2_esp32-s2-solo-2u_datasheet_en.pdf). See [here](https://www.espressif.com/sites/default/files/documentation/esp32-s2_datasheet_en.pdf) for the ESP32-S2 series documentation and [here](https://www.espressif.com/sites/default/files/documentation/esp32-s2_technical_reference_manual_en.pdf) for the ESP32-S2 technical reference manual.

### Boot modes

GPIO 46 (pin 16) is pulled low to avoid invalid configurations in boot pins. GPIO 0 (pin 27) is connected to the "B" pushbutton to allow switching between SPI (flash) boot and download (USB) boot. By default, it is pulled up, which selects SPI boot.

## Battery

The battery is a 400mAH 3.7V lithium-ion polymer battery.

## Peripherals

The FallCTF 2025 comes with a number of peripherals accessible from the ESP32 module via software. This is designed to be a comprehensive list for software developers working on the badge.

GPIO numbers are given for the ESP32 module. The relationship between pin numbers and IO port numbers are given in Table 3 on page 11 of the ESP32-S2-SOLO-2 datasheet.

### Overview

The following peripherals are available:
- USB (serial)
- two push buttons
- battery charge monitor
- SAO header
- buzzer
- joystick
- current sensor
- accelerometer
- display

### USB

USB D- is connected to GPIO 19 and D+ to GPIO 20 as required for "download boot", which is used to program the ESP32 over USB.

### Push buttons

"A" button is connected to GPIO 13 and "B" is connected to GPIO 0. Both buttons are pulled up by a 10K resistor and shorted to ground when depressed.

### Battery charge monitor

The battery is connected, through a pair of 100K resistors acting as a voltage divider, to GPIO 8. This allows for software to detect the battery charge via an ADC.

### SAO header

The SAO header shares an I2C connection with the accelerometer. SCL connected to GPIO 21 and SDA to GPIO 33. There are two SAO GPIO pins connected to GPIO 11 and GPIO 12.

### Buzzer

Both ends of the passive piezo buzzer are connected to the ESP32 through 220 Ohm resistors. One end is connected to GPIO 3 and the other to GPIO 9. We recommend grounding one of the pins and using the other as the PWM signal source.

### Joystick

The two axes of the joystick are connected to GPIO 4 and 5. The range is around from 0.8V to 1.4V. This varies by 2%-5% across devices.

The joystick has an internal variable resistance of 5K. One end is connected to an 8.2K resistor and the other end to a 820 Ohm resistor.

The exact part is [YTL YA13-FL7.4-B5Ka(45-10)-R-Y06](https://www.lcsc.com/datasheet/C37323742.pdf).

### Current sensor

There is a INA199A1DCKR ([datasheet](https://www.ti.com/lit/ds/symlink/ina199.pdf?ts=1758695550045)) connected to the 3.3V bus acting as a current sensor. It has a gain of 50 V/V. The output voltage is connected to GPIO 10. The current sensing resistor is 0.1 Ohms. To measure the operating current in Amps, use the formula `A = V / (I_R * G)`, where `A` is the operating current, `V` is the measured voltage in volts, `I_R` is the current sensing resistance (0.1 Ohms), and `G` is the gain (50 V/V).

From our testing, the current sensor is not very reliable and fluctuates wildly during use, reporting readings between 50% and 300%.

### Accelerometer

The STK8321 accelerometer ([datasheet](https://uploadcdn.oneyac.com/attachments/files/brand_pdf/sensortek/STK8321.pdf)) is attached to the same I2C lines as the SAO header (GPIO 21 and GPIO 33). The accelerometer's two interrupt pins are connected to GPIO 37 and GPIO 38. The slave address select pin is connected to GPIO 36. By default, this pin is pulled low, which selects the I2C address 0x0F. The chip supports a max I2C frequency of 400kHz.

Example initialization process:
- write 0xB6 to 0x14 (SWRST) to reset the chip
- write 0x03 to 0x0F (RANGESEL) to set the range to +/- 2g (this can be changed to 0x05 for +/- 4g or 0x08 for +/- 8g)
- write 0x0B to 0x10 (BWSEL) to set the bandwidth to 62.5Hz (this can be changed for different bandwidths)

For an example of code used to drive the accelerometer, see dev/accelerometer.py

### Display

The display is a 1.8" 128x160 color TFT LCD display with a ST7735S controller, sourced [from BuyDisplay](https://www.buydisplay.com/128x160-1-8-inch-color-tft-lcd-display-with-st7735-controller-spi). The controller datasheet is available [here](https://www.buydisplay.com/download/ic/ST7735S.pdf).

The following pins are connected:
- CS: GPIO 17
- RESET: GPIO 18
- DC: GPIO 7
- MOSI: GPIO 16
- SCK: GPIO 15
- LCD_LED: GPIO 41

The CS (chip select) and RESET pins are pulled high by default by the PCB. The DC and MOSI pins allow data and commands to be transmitted to the display controller. The SCK determines the clock speed. The datasheet specifies a max clock speed of 15Mhz, but we have found through testing that it supports a clock rate as high as 90Mhz (although values above 61Mhz do not appear to have any differences). In the final badge design, we used 40Mhz.

The LCD_LED pin is connected to a MOSFET which switches the backlight on and off. This pin can be driven with PWM to adjust the brightness of the backlight. We have found that a duty cycle between 20% and 40% offers a good visual experience.

## Design process and challenges

### Lessons learned

Here are some of the most important lessons I learned during the hardware design process:
- Use a circuit simulator (such as [falstad](https://www.falstad.com/circuit/circuitjs.html)). This is great especially if you don't have a solid grasp of basic electronics (like me at the start of this project). This allows you to catch basic mistakes such as flipped MOSFETs or incorrect resistor values.
- Design PCBs with plenty of room. In the prototyping stage, there's no need to squeeze everything together. Space out the traces to make reworking easier. This also makes it easier to debug and test the board.
- Order small batches. I ordered 10-15 boards at a time, which was unnecessary and wasteful. Ordering 5 boards at a time is sufficient for prototyping.

### Electrical problems

- USB shell
    - In v0.1, I connected the shell to ground through a 1M resistor. This was a mistake and removed in v0.2. The shell should be connected directly to ground.
- current limits
    - In v0.3, the LDO was only rated for 300mA, which is not enough to power the ESP32 at full Wi-Fi power. This was fixed in v1.0 by using a 500mA LDO.
- MOSFET direction
    - In v0.1, I was using the P-channel MOSFET in the wrong direction (swapped source and drain). This was fixed in v0.2, although this iteration had other problems (see below).
- MOSFET body diode
    - In v0.3, the body diode on the Q1 MOSFET allowed the 5V to inadvertently flow back to the battery, charging it. This was a problem as this spiked the current drawn from the USB port, causing it to shut off. This was fixed in v1.0 by using a second MOSFET (Q5). I made this mistake because I forgot about the body diode in a MOSFET and mistakenly believed that tying gate and source together would turn it off even if the drain was at a higher voltage than the source.
- swapped display backlight pins
    - In v0.2, I swapped the anode and cathode of the backlight LED. This was fixed in v0.3.

### Physical layout

- ESP32 module does not need to stick out of the board. This was recommended by the design, but some testing revealed that the antenna performance was not significantly affected by being surrounded by PCB material. The protruding design makes the badge more fragile and prone to damage.
- Switches not stick out too far from the edge of the board. Sometimes the 3D model can be misleading. Always check the physical size with the datasheet.
- In general, confirm the physical size of large parts to make sure they do not interfere with each other

### Part selection

Here is my general process for part selection:
- Choose parts that are commonly used and have good documentation. Avoid obscure parts that may be hard to source or have poor documentation.
- Prefer JLCPCB's basic parts, as they incur lower production costs.
- If there is a part you like that is too expensive, look for alternatives with the same specifications on multiple websites. Generally, most parts have "generic" versions that are significantly cheaper.

### JLCPCB PCBA capabilities

Keep in mind manufacturer's PCBA capabilities when designing the PCB, specifically when setting up the design rules. See [JLCPCB's capabilities](https://jlcpcb.com/capabilities/pcb-capabilities). In particular, the page on [extra fees](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra) states that the via inner hole size must be at least 0.3mm and the via outer diameter must be at least 0.4mm to qualify for no extra fees (note: the via hole size can be at least 0.2mm if the via diameter is at least 0.45mm).

### Lanyards

Lanyards weren't ordered in time for the competition. We ordered it the Monday before the competition (6 days prior), which was way too late. In future, we should order lanyards at least 3 weeks in advance.

### Lack of RAM

This is more of a software problem, but the underlying cause was hardware. We kept running out of RAM, as micropython by itself is very RAM-hungry. On top of that, the ESP Wi-Fi stack requires significant amount of memory as well. Adding to the problem is the fact that micropython runs as a task in ESP-IDF (which is based on FreeRTOS). This means that the micropython heap is separate from ESP-IDF's heap, and memory fragmentation can occur in both heaps. The solution was to freeze as much code as possible into the firmware, which reduces the amount of RAM needed at runtime. However, in future designs, we could use one of the ESP32 modules with embedded PSRAM (or even use a ESP32 SoC directly with external PSRAM).

### Improvements for future designs

- Separate user controllable (blue?) LED. No need for a power LED.
- Increase joystick voltage divider R39 and R40 to around 10K

## Final hardware design

### ESP32 module

Most of the design is pretty straightforward. There wasn't anything here that significantly differed from the recommended design in the datasheet.

### USB

We use several diodes for surge and ESD protection on the USB data and power lines. CC1 and CC2 are connected to ground through 5.1K resistors to indicate to the host that this is a USB 2.0 device, which allows it to draw up to 500mA from the host. The shell is connected directly to ground.

### Power regulation

This was by far the most complicated part of the design. The design went through several iterations before arriving at the current version, which uses two P-channel MOSFETs to switch between USB power and battery power. Notice that the Q1 MOSFET in the v1.0 schematic is actually "flipped" upside down: the source is at the bottom and the drain is at the top. There are three cases to consider:

- When both the USB and battery are connected. The 5V on the USB line causes the gate and source of Q1 to be at the same voltage (minus a small drop from the Schottky diode), so Q1 is turned off. This prevents current from flowing back to the battery, as there is separate dedicated circuitry to charge the battery. The 5V flows downstream to the LDO to power the rest of the badge.
- When only the USB is connected. The same logic as above applies, and the badge is powered from the USB line.
- When only the battery is connected. This is where it gets interesting. Depending on the state of SW1, the gate of Q5 is either tied to ground or to VBAT. If it is tied to ground, then Q5 is turned off and no current can flow past it. If it is tied to VBAT (which is also Q5's source), then Q5 is turned on and current can flow through Q5. From there, the current flows through the body diode of Q1 (which is oriented in the correct direction to allow current flow) and into the LDO to power the badge. The Schottky diode (D4) prevents current from flowing back to the USB line.

The Schottky diode can be used because the drop from 5V to 3.3V is large enough that the small drop across the diode (typically around 0.3V) does not matter. The resistors on the gate of each MOSFET are to prevent inrush current from damaging the MOSFET (I'm not sure if this is actually necessary, but it doesn't hurt). The pull-down resistor R2 is not necessary and is a remnant from an earlier design iteration.

The ME6211C33M5G 3.3V LDO I chose can handle up to 500mA of current, which is the recommended amount for the ESP32. In previous iterations, the LDO could only handle 300mA, which was not enough to power the badge when transmitting at full Wi-Fi power.

### Power indicator LED

Tuning the resistor on this LED was surprisingly tricky. I went from 680 -> 8.2K -> 13K. If the [datasheet](https://www.lcsc.com/datasheet/C2297.pdf) is to be trusted, the 13K resistor should result in a current of around 75uA, which is extremly dim (less than 2% of the intensity at 5mA, which is between 175 and 430 mcd with a 120 degree viewing angle).

### Battery charging

I used the TP4054 ([datasheet](https://media.digikey.com/pdf/Data%20Sheets/UTD%20Semi%20PDFs/TP4054.pdf)) for battery charge control. I used a 4.7K resistor to program the max charging current to 200mA, but that may have been too conservative. A better approach would be to allow the MCU to program this value (even something as simple as selecting between a "fast" and "slow" charge would have been better). There is some slightly more complicated circuitry to control the green and red charging LEDs, but those are straight from the datasheet. The resistor values have been tuned to reduce the brightness (since the LEDs are quite efficient).

### Buttons

Nothing special here. Standard 10K pull-up resistors.

### Joystick

Connected the joystick in series with a 8.2K on one side and a 820 Ohm resistor on the other side to offset the voltage divider so it sits nicely within the ESP32's ADC range (2.5V). This could have been improved by increasing the resistance slightly so that it fits in the `ADC_ATTEN_DB_6` range (which is 0V-1.3V). Currently the max is around 1.4V, which is slightly out of this narrower range.

### Accelerometer

Recommended design from the datasheet. Connecting the interrupts to the ESP32 was a nice feature, but unused.

### Current sensing

Fluctuates wildly. I'm not sure if the actual current is really so unstable or if I could have chose a better sensing resistor or amplifier.

### Buzzer

I connected both ends to the ESP32 through 220 Ohm resistors for greater flexibility in control. This allows the buzzer to be driven in a push-pull configuration, which would be twice as loud as driving it in a single-ended configuration. However, the buzzer is quite loud even when driven in a single-ended configuration, so this was unnecessary.

### Display

Besides connecting a N-channel MOSFET to be able to vary the backlight, everything else was straight from the datasheet.
