#!/usr/bin/env python


class uTorrentBridge:

    def _validate_property(self, property, module_1, module_2):
        # If module_1 property is an action
        if hasattr(getattr(module_1, property), 'action_required'):
            # If module_1 action is optional
            if not getattr(getattr(module_1, property), 'action_required', False):
                return True
            # If module_2 does not have action
            elif not hasattr(module_2, property):
                return False

        return True

    def __init__(self, *args, **kwargs):
        module = __import__('modules.%s' % kwargs['server']['module'], fromlist=('Server'))
        self.server = getattr(module, 'Server')(**kwargs['server'])

        module = __import__('modules.%s' % kwargs['client']['module'], fromlist=('Client'))
        self.client = getattr(module, 'Client')(**kwargs['client'])

        for property in dir(self.server):
            if not self._validate_property(property, self.server, self.client):
                raise NotImplementedError("Client module '%s' does not implement %s" % (self.client.__class__.__bases__[0].__name__, property))

        for property in dir(self.client):
            if not self._validate_property(property, self.client, self.server):
                raise NotImplementedError("Server module '%s' does not implement %s" % (self.server.__class__.__bases__[0].__name__, property))

        self.client.server = self.server
        self.server.client = self.client

    def start(self):
        self.server._start()

    def stop(self):
        self.server._stop()

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    (options, args) = parser.parse_args()

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
