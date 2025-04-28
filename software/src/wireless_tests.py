import machine
import network
import espmesh


def event_handler(event):
    print('event:', event)

def main():
    print('hello')
    '''
    import espmesh; e = espmesh.ESPMesh()
    e.active()
    '''
    e = espmesh.ESPMesh()
    print('INFO: ESPMesh object created')
    # e.register_event_handler(event_handler)
    e.config(
        ssid='Nix Kingdom',
        password='archpeasants',
        channel=1,
        ap_password='e8vrbngAscjv',
    )
        
    e.active(True)
    print('INFO: ESPMesh active')


if __name__ == '__main__':
    # main()
    pass
