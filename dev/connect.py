import asyncio
import time

from layout import Style
from view import BasicTextView
from menu import Runnable, ListMenu, menu_with_text
from wireless import Wireless

from logger import log


class ConnectMenuState:
    SCANNING = 0
    CONFIRM = 1
    HOST_CONN_REQ = 2
    HOST = 3
    CLIENT = 4
    GOBACK = 5
    CONN_FAILED = 6


class ConnectMenu(Runnable):
    RECENT_PEERS_TIMEOUT_MS = 2000
    PEERLIST_REFRESH_MS = 500
    MIN_RSSI = -70 # minimum RSSI to show peer

    def __init__(self, device_io: 'DeviceIO'):
        self.device_io = device_io
        self._recent_peers = []
        self._cancel_menu_event = asyncio.Event()
        self._state = ConnectMenuState.SCANNING
        self._pending_peer = None
        self._last_refresh = 0

    def wireless_event(self, msg, host, rssi):
        if msg == b'ADV' and self._state == ConnectMenuState.SCANNING:
            peer = (rssi, time.ticks_ms(), host)

            # update existing peer or add new one
            for i, p in enumerate(self._recent_peers):
                if p[2] == host:
                    self._recent_peers[i] = peer
                    break
            else:
                self._recent_peers.append(peer)

            # sort by RSSI (higher is better)
            self._recent_peers.sort(reverse=True, key=lambda p: p[0])

            self._refresh_peerlist()
        elif msg == b'CONN_ACK' and self._state == ConnectMenuState.HOST_CONN_REQ and host == self._pending_peer:
            log(f'Received CONN_ACK from {host.hex()}')
            self._state = ConnectMenuState.HOST
        else:
            log(f'ConnectMenu received unknown wireless msg from {host.hex()}: {msg}')

    def _state_change_func(self, new_state, new_pending_peer=None):
        def inner():
            self._state = new_state
            if new_pending_peer is not None:
                self._pending_peer = new_pending_peer
        return inner

    def _refresh_peerlist(self):
        if self._state == ConnectMenuState.SCANNING:
            # check if we are refreshing too often
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_refresh) >= self.PEERLIST_REFRESH_MS:
                # end the current menu run to trigger a refresh
                self._cancel_menu_event.set()
                self._last_refresh = now
        else:
            log(f'WARNING: invalid condition to refresh peerlist (state={self._state})', level='test')

    async def _run_menu(self):
        past_menu = None
        while self._state == ConnectMenuState.SCANNING:
            items = [('Back', None, self._state_change_func(ConnectMenuState.GOBACK))]
            for rssi, ts, mac in self._recent_peers:
                if rssi >= self.MIN_RSSI:
                    msg = f'{Wireless.mac_to_usable(mac)} {self.device_io.wireless.rssi_to_display(rssi)}'
                    next_state_confirm = self._state_change_func(ConnectMenuState.CONFIRM, new_pending_peer=mac)
                    items.append((msg, None, next_state_confirm))
            text_view = BasicTextView(self.device_io.display)
            text_view.update(0, f'Your id: {Wireless.mac_to_usable(self.device_io.wireless.my_mac())}')
            text_view.update(2, 'Select a peer:')
            self._cancel_menu_event.clear()
            past_menu = ListMenu(
                self.device_io,
                items,
                # use old menu's selected index if possible
                init_selected=min(past_menu.select_idx - past_menu.menu_start
                                  if past_menu else 0, max(len(items)-1, 0)),
                prepended_views=[(text_view, Style(posType=0b01, y=5))], # relative y with 5px top margin
                cancel_event=self._cancel_menu_event
            )
            await past_menu.run()

    async def _run_advertise(self):
        adv_interval_ms = 500
        while self._state == ConnectMenuState.SCANNING:
            self.device_io.wireless.advertise()
            for _ in range(adv_interval_ms // 50):
                if self._state != ConnectMenuState.SCANNING:
                    return
                await asyncio.sleep_ms(50)

            # filter out old peers
            now = time.ticks_ms()
            new_recent_peers = [
                p for p in self._recent_peers if time.ticks_diff(now, p[1]) < self.RECENT_PEERS_TIMEOUT_MS
            ]
            if len(new_recent_peers) != len(self._recent_peers):
                self._recent_peers = new_recent_peers
                self._refresh_peerlist()


    async def run(self):
        self.device_io.wireless.subscribe(self.wireless_event)

        while True:
            log(f'ConnectMenu state: {self._state}')
            if self._state == ConnectMenuState.SCANNING:
                self._recent_peers = []
                self._pending_peer = None

                # reboot wifi if not active
                if self.device_io.wireless.is_active:
                    self.device_io.wireless.down()
                self.device_io.wireless.up()

                # run advertise and menu concurrently
                await asyncio.gather(self._run_advertise(), self._run_menu())
            elif self._state == ConnectMenuState.GOBACK:
                log('Going back from ConnectMenu')
                break
            elif self._state == ConnectMenuState.CONFIRM:
                await menu_with_text(
                    self.device_io,
                    ['Connect to', f'{Wireless.mac_to_usable(self._pending_peer)}?'],
                    [
                        ('Yes', None, self._state_change_func(ConnectMenuState.HOST_CONN_REQ)),
                        ('No', None, self._state_change_func(ConnectMenuState.SCANNING)),
                    ]
                )
            elif self._state == ConnectMenuState.HOST_CONN_REQ:
                self.device_io.wireless.send(self._pending_peer, b'CONN_REQ', sync=False)
                self._cancel_menu_event.clear()
                await menu_with_text(
                    self.device_io,
                    ['Connecting...'],
                    [
                        ('Cancel', None, self._state_change_func(ConnectMenuState.SCANNING)),
                    ],
                    cancel_event=self._cancel_menu_event
                )
            elif self._state == ConnectMenuState.HOST:
                self._cancel_menu_event.clear()
                host_menu = menu_with_text(
                    self.device_io,
                    ['Connected to', f'{Wireless.mac_to_usable(self._pending_peer)}'],
                    [
                        ('Disconnect', None, self._state_change_func(ConnectMenuState.GOBACK)),
                    ],
                    cancel_event=self._cancel_menu_event
                )
                await host_menu.run()
            elif self._state == ConnectMenuState.CONN_FAILED:
                await menu_with_text(
                    self.device_io,
                    ['Connection failed', 'or lost'],
                    [
                        ('OK', None, self._state_change_func(ConnectMenuState.SCANNING)),
                    ]
                )
            else:
                await menu_with_text(
                    self.device_io,
                    ['Unknown state in', f'ConnectMenu: {self._state}'],
                    [
                        ('OK', None, self._state_change_func(ConnectMenuState.GOBACK)),
                    ]
                )

        # stop wifi to save power
        if self.device_io.wireless.is_active:
            self.device_io.wireless.down()
        else:
            log('WARNING: Wireless was already down when exiting ConnectMenu', level='test')

        self.device_io.wireless.unsubscribe(self.wireless_event)
