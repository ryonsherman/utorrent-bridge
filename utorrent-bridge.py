#!/usr/bin/env python


class uTorrentBridge:

    def __init__(self, *args, **kwargs):
        module = __import__('modules.%s' % kwargs['client']['module'], fromlist=('Client'))
        client = getattr(module, 'Client')
        self.client = client(**kwargs['client'])

        module = __import__('modules.%s' % kwargs['server']['module'], fromlist=('Server'))
        server = getattr(module, 'Server')
        self.server = server(**kwargs['server'])

        self.client.server = self.server
        self.server.client = self.client

    def start(self):
        self.server._start()

    def stop(self):
        self.server._stop()

if __name__ == '__main__':
    from ConfigParser import SafeConfigParser
    config = SafeConfigParser()
    config.read('config.conf')

    from collections import defaultdict
    client = defaultdict(list, config.items('client'))
    server = defaultdict(list, config.items('server'))

    bridge = uTorrentBridge(client=client, server=server)
    try:
        bridge.start()
    except KeyboardInterrupt:
        bridge.stop()
