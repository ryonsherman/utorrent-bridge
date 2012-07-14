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

    _transfer_methods = {
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

    _file_methods = {
        'f.get_path': ['name'],
        'f.get_size_bytes': ['size'],
        'f.get_completed_chunks': ['size_downloaded'],
        'f.get_priority': ['priority']
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
            for field in self.server.Transfer._fields:
                for method in self._transfer_methods:
                    if field in self._transfer_methods[method]:
                        calls.append({'methodName': method, 'params': [hash]})
                        fields[hash].append(field)
                        break

        values = [value[0] for value in self._rpc._multicall(calls)]

        transfers = []
        for hash in hashes:
            transfer = self.server.Transfer()
            transfer.hash = hash

            for field in transfer._fields:
                for method in self._transfer_methods:
                    if field in self._transfer_methods[method]:
                        setattr(transfer, field, values.pop(0))
                        break
            transfers.append(transfer)

        return transfers

    @Action.required
    def get_files(self, hash):
        hashes = [hash] if type(hash) is str else hash
        file_count = [value[0] for value in self._rpc.call('d.get_size_files', hashes)]
        hashes = dict(zip(hashes, file_count))

        calls = []
        for hash, file_count in hashes.iteritems():
            for i in range(file_count):
                for field in self.server.File._fields:
                    for method in self._file_methods:
                        if field in self._file_methods[method]:
                            calls.append({'methodName': method, 'params': [hash, i]})
                            break

        values = [value[0] for value in self._rpc._multicall(calls)]

        files = {}
        for hash, file_count in hashes.iteritems():
            files[hash] = []
            for i in range(file_count):
                file = self.server.File()
                for field in file._fields:
                    for method in self._file_methods:
                        if field in self._file_methods[method]:
                            setattr(file, field, values.pop(0))
                            break
                files[hash].append(file)

        return files

    @Action.required
    def get_properties(self, hash):
        pass

    @Action.required
    def add_url(self, url):
        self._rpc.call('load', url, False if type(url) is str else True)

    @Action.required
    def start(self, hash):
        self._rpc.call('start', hash, False if type(hash) is str else True)

    @Action.required
    def stop(self, hash):
        self._rpc.call('close', hash, False if type(hash) is str else True)

    @Action.optional
    def pause(self, hash):
        self._rpc.call('stop', hash, False if type(hash) is str else True)

    @Action.optional
    def unpause(self, hash):
        self._rpc.call('resume', hash, False if type(hash) is str else True)

    @Action.optional
    def recheck(self, hash):
        self._rpc.call('check_hash', hash, False if type(hash) is str else True)

    @Action.required
    def remove(self, hash):
        self._rpc.call('erase', hash, False if type(hash) is str else True)

    @Action.optional
    def restart(self, hash):
        self.stop(hash)
        self.start(hash)


class Server(rTorrent, Server):

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
