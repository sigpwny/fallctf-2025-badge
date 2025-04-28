import machine


"""
ESP32S2 board UART connector. Connects to a UART RX/TX on two given
pins and forwards data to micropython REPL.
"""

RX_PIN = 18
TX_PIN = 17
BAUDRATE = 115200
STOPBITS = 1
PARITY = None

uart = machine.UART(1, baudrate=BAUDRATE, rx=RX_PIN, tx=TX_PIN, stop=STOPBITS, parity=PARITY)
uart.init(baudrate=BAUDRATE, rx=RX_PIN, tx=TX_PIN, stop=STOPBITS, parity=PARITY)
print('UART initialized')


# uart = machine.UART(1); uart.init(baudrate=115200, rx=18, tx=17, stop=1, parity=None)

while True:
    if uart.any():
        try:
            data = uart.read()
            decoded = data.decode('utf-8')
            print(decoded, end='')
        except UnicodeError:
            print(data)
    else:
        pass
