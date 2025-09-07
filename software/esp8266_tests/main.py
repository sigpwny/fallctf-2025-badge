import machine
import network
import espnow
import random
import time

BROADCAST_PEER = b'\xff\xff\xff\xff\xff\xff'

def pairing_test():
    print('hello, ptest!')

    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)  # Or network.WLAN.IF_AP
    sta.active(True)
    sta.disconnect()      # For ESP8266

    e = espnow.ESPNow()
    e.active(True)

    try:
        e.add_peer(BROADCAST_PEER)      # Must add_peer() before send()
    except OSError as err:
        if err.args[0] == espnow.ESP_ERR_ESPNOW_EXIST:
            pass

    devices = {}
    cycles = 0

    while True:
        cycles += 1
        e.send(BROADCAST_PEER, "Pairing request")
        #print('sent pairing request')
        resps = e.recv(timeout_ms = random.randint(400, 600))

        if resps == (None, None):
            continue

        devices[resps[0]] = cycles

        print('devices:')
        for addr, count in devices.items():
            if count + 5 < cycles:
                del devices[addr]
            print(f'  {addr.hex()}: {count}')

        
        time.sleep(2)

def board1_main():
    print('hello, board1!')

    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)  # Or network.WLAN.IF_AP
    sta.active(True)
    sta.disconnect()      # For ESP8266

    e = espnow.ESPNow()
    e.active(True)
    peer = bytes.fromhex('244cab519ad2')   # MAC address of peer's wifi interface
    e.add_peer(peer)      # Must add_peer() before send()

    e.send(peer, "Starting...")
    for i in range(100):
        e.send(peer, str(i)*20, True)
    e.send(peer, b'end')


def board2_main():
    print('hello, board2!')

    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)
    sta.active(True)
    sta.disconnect()   # Because ESP8266 auto-connects to last Access Point

    # print my MAC address
    print('mac address:', sta.config('mac').hex())

    e = espnow.ESPNow()
    e.active(True)

    while True:
        host, msg = e.recv()
        if msg:             # msg == None if timeout in recv()
            print('got message from', host.hex(), 'msg:', msg)
            if msg == b'end':
                break


def main():
    print('my board id is', machine.unique_id().hex())

    pairing_test()
    # board1_id = bytes.fromhex('68b6b311c17a')
    # board2_id = bytes.fromhex('68b6b3120870')

    # if machine.unique_id() == board1_id:
    #     board1_main()
    # elif machine.unique_id() == board2_id:
    #     board2_main()
    # else:
    #     print('unknown board')


if __name__ == '__main__':
    main()
