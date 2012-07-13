from lib import Action, Interface
from lib.client import Client
from lib.server import Server


class rTorrent(Interface):

    BUILD = '0.9.2'

    @Action.optional
    def recheck(self, hash):
        raise NotImplementedError


class Client(rTorrent, Client):

    class RPC:

        @property
        def _multicall(self):
            return self._rpc.system.multicall

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

    @Action.required
    def get_transfers(self, views=['main']):
        hashes = self._rpc.call('download_list', views, False) or []

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

    @Action.required
    def add_url(self, url):
        self._rpc.call('load', url)

    @Action.required
    def start(self, hash):
        self._rpc.call('d.start', hash)

    @Action.required
    def stop(self, hash):
        self._rpc.call('d.close', hash)

    @Action.optional
    def pause(self, hash):
        self._rpc.call('d.stop', hash)

    @Action.optional
    def unpause(self, hash):
        self._rpc.call('d.resume', hash)

    @Action.optional
    def recheck(self, hash):
        self._rpc.call('d.check_hash', hash)

    @Action.required
    def remove(self, hash):
        self._rpc.call('d.erase', hash)

    @Action.optional
    def restart(self, hash):
        self.stop(hash)
        self.start(hash)


class Server(rTorrent, Server):

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
