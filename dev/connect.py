import asyncio
import random
import time

from layout import Style
from view import BasicTextView
from menu import Runnable, ListMenu, menu_with_text
from wireless import Wireless

from logger import log


class ConnectMenuState:
    SCANNING            = 0
    CONFIRM             = 1
    HOST_CONN_REQ       = 2
    READY_TO_BATTLE     = 3
    CLIENT_CONN_CONFIRM = 4
    GOBACK              = 5
    CONN_FAILED         = 6
    BATTLE              = 7
    DISCONNECT          = 8


class ConnectMenu(Runnable):
    RECENT_PEERS_TIMEOUT_MS = 2000
    PEERLIST_REFRESH_MS = 500
    MIN_RSSI = -70 # minimum RSSI to show peer

    def __init__(self, device_io: 'DeviceIO'):
        self.device_io = device_io
        self._recent_peers = []
        self._cancel_menu_event = asyncio.Event()
        self._state = ConnectMenuState.SCANNING
        self._peer = None
        self._last_refresh = 0
        self._battle = None
        self._my_random_seed = None
        self._combined_random_seed = 0
        self._host_side = None

    def _wireless_event(self, msg, host, rssi):
        # log(f'ConnectMenu received wireless event from {host.hex()}: {msg} (rssi={rssi}), state={self._state}')

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
        elif msg == b'CONN_REQ' and self._state in [
                ConnectMenuState.SCANNING,
                ConnectMenuState.CONFIRM,
                ConnectMenuState.CONN_FAILED
            ]:
            log(f'Received CONN_REQ from {host.hex()}')
            self._peer = host
            self._state = ConnectMenuState.CLIENT_CONN_CONFIRM
            self._cancel_menu_event.set() # cancel current menu to show connection request
            self._host_side = False
        elif host == self._peer:
            if msg == b'CONN_ACK' and self._state == ConnectMenuState.HOST_CONN_REQ:
                log(f'Received CONN_ACK from {host.hex()}')
                self._state = ConnectMenuState.READY_TO_BATTLE
                self._cancel_menu_event.set() # end "Connecting..." menu
                self._host_side = True
            elif msg == b'DISCONNECT' and self._state in [
                    ConnectMenuState.READY_TO_BATTLE,
                    ConnectMenuState.HOST_CONN_REQ,
                    ConnectMenuState.CLIENT_CONN_CONFIRM
                ]:
                log(f'Received DISCONNECT from {host.hex()}')
                self._state = ConnectMenuState.CONN_FAILED
                self._cancel_menu_event.set() # end current menu
            elif msg.startswith(b'BATTLE_INFO') and self._state == ConnectMenuState.READY_TO_BATTLE:
                log(f'Received {msg} from {host.hex()}')
                data = msg[len(b'BATTLE_INFO'):]
                other_random_seed = int.from_bytes(data[0:4], 'little')
                self._combined_random_seed = self._my_random_seed ^ other_random_seed
                self._my_random_seed = None
                other_stats_data = data[4:]
                try:
                    from battle import BattleStats, BattleRunner
                    other_stats = BattleStats.deserialize(other_stats_data)
                    my_stats = self.device_io.ship_stats.get_battle_stats()
                    self._battle = BattleRunner(self.device_io, my_stats, other_stats)
                    self._state = ConnectMenuState.BATTLE
                    self._cancel_menu_event.set() # end "Starting battle..." menu
                except Exception as e:
                    log(f'Error deserializing other stats or starting battle: {e}', level='error')
                    self._state = ConnectMenuState.CONN_FAILED
                    self._cancel_menu_event.set()
            else:
                log(f'ConnectMenu received unknown wireless msg from {host.hex()}: {msg}')

    def _state_change_func(self, new_state, new_pending_peer=None, send_msg=None):
        def inner():
            if send_msg is not None and self._peer is not None:
                self.device_io.wireless.send(self._peer, send_msg, sync=False)
            self._state = new_state
            if new_pending_peer is not None:
                self._peer = new_pending_peer
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
        self.device_io.wireless.subscribe(self._wireless_event)

        while True:
            log(f'ConnectMenu state: {self._state}')
            if self._state == ConnectMenuState.SCANNING:
                self._recent_peers = []
                self._peer = None
                self._host_side = None

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
                self._cancel_menu_event.clear()
                await menu_with_text(
                    self.device_io,
                    ['Connect to', f'{Wireless.mac_to_usable(self._peer)}?'],
                    [
                        ('Yes', None, self._state_change_func(ConnectMenuState.HOST_CONN_REQ)),
                        ('No', None, self._state_change_func(ConnectMenuState.SCANNING)),
                    ],
                    cancel_event=self._cancel_menu_event
                )
            elif self._state == ConnectMenuState.HOST_CONN_REQ:
                self.device_io.wireless.send(self._peer, b'CONN_REQ', sync=False)
                self._cancel_menu_event.clear()
                await menu_with_text(
                    self.device_io,
                    ['Connecting...'],
                    [('Cancel', None, self._state_change_func(ConnectMenuState.SCANNING, send_msg=b'DISCONNECT'))],
                    cancel_event=self._cancel_menu_event
                )
            elif self._state == ConnectMenuState.READY_TO_BATTLE:
                stats = self.device_io.ship_stats.get_battle_stats().serialize()
                self._my_random_seed = random.getrandbits(32)
                random_seed = self._my_random_seed.to_bytes(4, 'little')
                self.device_io.wireless.send(self._peer, b'BATTLE_INFO' + random_seed + stats, sync=False)
                self._cancel_menu_event.clear()
                await menu_with_text(
                    self.device_io,
                    ['Starting battle...'],
                    [('Cancel', None, self._state_change_func(ConnectMenuState.SCANNING, send_msg=b'DISCONNECT'))],
                    cancel_event=self._cancel_menu_event
                )
            elif self._state == ConnectMenuState.CLIENT_CONN_CONFIRM:
                self._cancel_menu_event.clear()
                await menu_with_text(
                    self.device_io,
                    ['Connection request', f'from {Wireless.mac_to_usable(self._peer)}'],
                    [
                        ('Accept', None, self._state_change_func(ConnectMenuState.READY_TO_BATTLE, send_msg=b'CONN_ACK')),
                        ('Decline', None, self._state_change_func(ConnectMenuState.SCANNING, send_msg=b'DISCONNECT'))
                    ],
                    cancel_event=self._cancel_menu_event
                )
            elif self._state == ConnectMenuState.CONN_FAILED or self._state == ConnectMenuState.DISCONNECT:
                msgs = ['Connection failed' if self._state == ConnectMenuState.CONN_FAILED else 'Disconnected']
                if self._peer is not None:
                    msgs.append(f'with peer: {Wireless.mac_to_usable(self._peer)}')
                await menu_with_text(
                    self.device_io,
                    msgs,
                    [('OK', None, self._state_change_func(ConnectMenuState.SCANNING)),]
                )
            elif self._state == ConnectMenuState.BATTLE:
                if self._battle is not None:
                    await self._battle.run(switch_side=self._host_side, seed=self._combined_random_seed, opp=self._peer)
                    self._combined_random_seed = None
                    self._battle = None
                    self._host_side = None
                self._state = ConnectMenuState.GOBACK
            else:
                await menu_with_text(
                    self.device_io,
                    ['Unknown state in', f'ConnectMenu: {self._state}'],
                    [('OK', None, self._state_change_func(ConnectMenuState.GOBACK)),]
                )

        # stop wifi to save power
        if self.device_io.wireless.is_active:
            self.device_io.wireless.down()
        else:
            log('WARNING: Wireless was already down when exiting ConnectMenu', level='test')

        self.device_io.wireless.unsubscribe(self._wireless_event)
