import machine
import network
import espnow
import time


def main():
    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)
    sta.active(True)
    # max power: generally 14.50-14.75 dBm
    sta.config(txpower=14.50)

    # print my MAC address
    print('mac address:', sta.config('mac').hex())

    print('0')
    esp = espnow.ESPNow()
    print('1')
    esp.active(True)
    print('2')

    peer = bytes.fromhex('ff' * 6)
    # peer = bytes.fromhex('244cab519ad2')
    print('3')
    esp.add_peer(peer)
    print('4')
    print(esp.get_peers())
    print('5')

    try:
        time.sleep(0.3)

        res1 = esp.send(peer, "hello, world")
        res2 = esp.recv(0)
        print('got', res1, res2)
    except Exception as e:
        print('Error:', e)

    print('done')

    time.sleep(0.2)

    esp.active(False)

    while True:
        time.sleep(1)


if __name__ == '__main__':
    time.sleep(2)
    main()
