import machine
import network
import espnow


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
    board1_id = bytes.fromhex('ef845100')
    board2_id = bytes.fromhex('d29a5100')

    if machine.unique_id() == board1_id:
        board1_main()
    elif machine.unique_id() == board2_id:
        board2_main()
    else:
        print('unknown board')


if __name__ == '__main__':
    main()
