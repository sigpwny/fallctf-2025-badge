import asyncio
import time

from layout import Style
from view import BasicTextView
from menu import Runnable, ListMenu
from wireless import Wireless

from logger import log


class ConnectMenuState:
    SCANNING = 0
    CONFIRM = 1
    CONNECTED = 2
    GOBACK = 3


class ConnectMenu(Runnable):
    RECENT_PEERS_TIMEOUT_MS = 2000
    PEERLIST_REFRESH_MS = 500
    MIN_RSSI = -70 # minimum RSSI to show peer

    def __init__(self, device_io: 'DeviceIO'):
        self.device_io = device_io
        self._recent_peers = []
        self._peerlist_menu = None
        self._state = ConnectMenuState.SCANNING
        self._pending_peer = None
        self._last_refresh = 0

    def wireless_event(self, event_type, value):
        if event_type == 'adv' and self._state == ConnectMenuState.SCANNING:
            peer = (value['rssi'], time.ticks_ms(), value['mac'])

            # update existing peer or add new one
            for i, p in enumerate(self._recent_peers):
                if p[2] == peer[2]:
                    self._recent_peers[i] = peer
                    break
            else:
                self._recent_peers.append(peer)

            # sort by RSSI (higher is better)
            self._recent_peers.sort(reverse=True, key=lambda p: p[0])

            self._refresh_peerlist()

    def _state_change_func(self, new_state, new_pending_peer=None):
        def inner():
            self._state = new_state
            if new_pending_peer is not None:
                self._pending_peer = new_pending_peer
        return inner

    def _refresh_peerlist(self):
        if self._peerlist_menu and self._state == ConnectMenuState.SCANNING:
            # check if we are refreshing too often
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_refresh) >= self.PEERLIST_REFRESH_MS:
                # end the current menu run to trigger a refresh
                self._peerlist_menu.keep_running = False
                self._last_refresh = now
        else:
            log(f'WARNING: invalid condition to refresh peerlist (peerlist_menu={self._peerlist_menu}, state={self._state})', level='test')

    async def _run_menu(self):
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
            self._peerlist_menu = ListMenu(
                self.device_io,
                items,
                # use old menu's selected index if possible
                init_selected=min(self._peerlist_menu.select_idx - self._peerlist_menu.menu_start
                                  if self._peerlist_menu else 0, max(len(items)-1, 0)),
                prepended_views=[(text_view, Style(posType=0b01, y=5))], # relative y with 5px top margin
            )
            await self._peerlist_menu.run()

    async def _run_advertise(self):
        while self._state == ConnectMenuState.SCANNING:
            self.device_io.wireless.advertise()
            await asyncio.sleep_ms(500)

            # filter out old peers
            now = time.ticks_ms()
            new_recent_peers = [
                p for p in self._recent_peers if time.ticks_diff(now, p[1]) < self.RECENT_PEERS_TIMEOUT_MS
            ]
            if len(new_recent_peers) != len(self._recent_peers):
                self._recent_peers = new_recent_peers
                self._refresh_peerlist()


    async def run(self):
        self.device_io.wireless.subscribe(self.wireless_event, events=['adv'])

        # start wifi
        if not self.device_io.wireless.is_active:
            self.device_io.wireless.up()

        while True:
            if self._state == ConnectMenuState.SCANNING:
                self._recent_peers = []
                self._peerlist_menu = None
                self._pending_peer = None
                # run advertise and menu concurrently
                await asyncio.gather(self._run_advertise(), self._run_menu())
            elif self._state == ConnectMenuState.GOBACK:
                log('Going back from ConnectMenu')
                break
            elif self._state == ConnectMenuState.CONFIRM:
                text_view = BasicTextView(self.device_io.display)
                text_view.update(0, f'Confirm connect to')
                text_view.update(1, f'{Wireless.mac_to_usable(self._pending_peer)}?')
                confirm_menu = ListMenu(
                    self.device_io,
                    [
                        ('Yes', None, self._state_change_func(ConnectMenuState.CONNECTED)),
                        ('No', None, self._state_change_func(ConnectMenuState.SCANNING)),
                    ],
                    prepended_views=[(text_view, Style(posType=0b01, y=5))] # relative y with 5px top margin
                )
                await confirm_menu.run()
            elif self._state == ConnectMenuState.CONNECTED:
                log('Connected!')
                # TODO: send connection request and wait for response
                text_view = BasicTextView(self.device_io.display)
                text_view.update(0, f'Game is loading...')
                await ListMenu(
                    self.device_io,
                    [
                        ('Cancel', None, self._state_change_func(ConnectMenuState.GOBACK)),
                    ],
                    prepended_views=[(text_view, Style(posType=0b01, y=5))] # relative y with 5px top margin
                ).run()

        # stop wifi to save power
        if self.device_io.wireless.is_active:
            self.device_io.wireless.down()
        else:
            log('WARNING: Wireless was already down when exiting ConnectMenu', level='test')

        self.device_io.wireless.unsubscribe(self.wireless_event, events=['adv'])
