from lib.client import Client
from lib.server import Server


class rTorrent:

    BUILD = '0.9.2'

    # def get_transfers()

    # def action_add_url()
    # def action_start()
    # def action_stop()
    # def action_pause()
    # def action_unpause()
    # def action_recheck()
    # def action_remove()
    # def action_restart()


class Client(Client):

    class RPC:

        def __init__(self, address, port):
            from xmlrpclib import Server

            self._rpc = Server("http://%s:%s/RPC2" % (address, port))

        def call(self, method, params, multicall=True):
            if type(params) == list and multicall:
                return self.multicall(method, params)
            else:
                return getattr(self._rpc, method)(params)

        def multicall(self, method, params):
            calls = []
            for param in params:
                calls.append({'methodName': method, 'params': [param]})
            return self._multicall(calls)

        def _multicall(self, calls):
            return self._rpc.system.multicall(calls)

    _methods = {
        'd.get_state': ['status'],
        'd.get_name': ['name'],
        'd.get_size_bytes': ['size'],
        'd.get_completed_bytes': ['downloaded'],
        'd.get_up_total': ['uploaded'],
        'd.get_ratio': ['ratio'],
        'd.get_up_rate': ['upload_speed'],
        'd.get_down_rate': ['download_speed'],
        'd.get_peers_accounted': ['peers_connected'],
        'd.get_peers_complete': ['seeds_connected'],
        'd.get_left_bytes': ['remaining']
    }

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

        self._rpc = self.RPC(self.address, self.port)

    def get_transfers(self, views=['main']):
        hashes = self._rpc.call('download_list', views, False)

        calls = []
        fields = {}
        for hash in hashes:
            fields[hash] = []
            for field in dir(self.server.Transfer):
                for method in self._methods.keys():
                    if field in self._methods[method]:
                        calls.append({'methodName': method, 'params': [hash]})
                        fields[hash].append(field)

        transfers = []
        if calls:
            values = self._rpc._multicall(calls)

            index = 0
            for hash in hashes:
                transfer = self.server.Transfer()
                transfer.hash = hash

                for field in fields[hash]:
                    setattr(transfer, field, values[index][0])
                    index += 1

                transfers.append(transfer)

        return transfers

    def action_start(self, hashes):
        self._rpc.call('d.start', hashes)

    def action_stop(self, hashes):
        self._rpc.call('d.close', hashes)

    def action_pause(self, hashes):
        self._rpc.call('d.stop', hashes)

    def action_unpause(self, hashes):
        self._rpc.call('d.resume', hashes)

    def action_recheck(self, hashes):
        self._rpc.call('d.check_hash', hashes)

    def action_remove(self, hashes):
        self._rpc.call('d.erase', hashes)

    def action_restart(self, hashes):
        self.action_stop(hashes)
        self.action_start(hashes)

    def action_add_url(self, urls):
        self._rpc.call('load', urls)


class Server(Server):

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
