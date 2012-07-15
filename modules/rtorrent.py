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

        def call(self, method, params, multicall=False):
            if type(params) == list and multicall:
                response = self._multicall([{'methodName': method, 'params': [param]} for param in params])
            else:
                response = getattr(self._rpc, method)(params)

            if self.log:
                from datetime import datetime
                open(self.log, 'a+b').write("[%s] %s\n" % (datetime.now(), str(response)))

            return response

        def multicall(self, methods):
            # TODO: pass dict of methods, replace _rpc._multicall calls
            for method, params in methods.items():
                pass

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
        '_file_size_downloaded': ['size_downloaded'],
        'f.get_priority': ['priority']
    }

    _property_methods = {
        '_property_trackers': ['trackers'],
        'get_upload_rate': ['ulrate'],
        'get_download_rate': ['dlrate'],
        '_property_dht':  ['dht'],
        'get_peer_exchange': ['pex'],
        'get_max_uploads': ['ulslots'],
    }

    def _file_size_downloaded(self, hash, index):
        calls = [
            {'methodName': 'f.get_size_bytes', 'params': [hash, index]},
            {'methodName': 'f.get_size_chunks', 'params': [hash, index]},
            {'methodName': 'f.get_completed_chunks', 'params': [hash, index]}
        ]
        size, chunks_total, chunks_completed = [value[0] for value in self._rpc._multicall(calls)]

        return (size / chunks_total) * chunks_completed

    def _property_trackers(self, hash):
        if type(hash) is str:
            tracker_count = self._rpc.call('d.get_tracker_size', hash)

            calls = []
            for i in range(tracker_count):
                calls.append({'methodName': 't.get_url', 'params': [hash, i]})

            return "\n".join(self._rpc._multicall(calls)[0])
        else:
            tracker_count = [value[0] for value in self._rpc.call('d.get_tracker_size', hash, True)]
            hashes = dict(zip(hash, tracker_count))

            calls = []
            for hash, tracker_count in hashes.items():
                for i in range(tracker_count):
                    calls.append({'methodName': 't.get_url', 'params': [hash, i]})

            return dict(zip(hashes, ["\n".join(value) for value in self._rpc._multicall(calls)]))

    def _property_dht(self, hash):
        if type(hash) is str:
            return self._rpc.call('dht_statistics', hash).get('active')
        else:
            return dict(zip(hash, [value['active'] for value in self._rpc.call('dht_statistics', hash, True)]))

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

        self._rpc = self.RPC(self.address, self.port)
        self._rpc.log = kwargs.get('log')

    @Action.required
    def get_transfers(self, views=['main']):
        hashes = self._rpc.call('download_list', views) or []

        calls = []
        call_values = []
        for hash in hashes:
            for field in self.server.Transfer._fields:
                for method in self._transfer_methods:
                    if field in self._transfer_methods[method]:
                        if getattr(self, method, False):
                            call_values.append(getattr(self, method)(hash))
                        else:
                            calls.append({'methodName': method, 'params': [hash]})
                        break

        multicall_values = [value[0] for value in self._rpc._multicall(calls)]

        transfers = []
        for hash in hashes:
            transfer = self.server.Transfer()
            transfer.hash = hash

            for field in transfer._fields:
                for method in self._transfer_methods:
                    if field in self._transfer_methods[method]:
                        setattr(transfer, field, call_values.pop(0) if getattr(self, method, False) else  multicall_values.pop(0))
                        break
            transfers.append(transfer)

        return transfers

    @Action.required
    def get_files(self, hash):
        hashes = [hash] if type(hash) is str else hash
        file_count = [value[0] for value in self._rpc.call('d.get_size_files', hashes, True)]
        hashes = dict(zip(hashes, file_count))

        calls = []
        call_values = []
        for hash, file_count in hashes.items():
            for i in range(file_count):
                for field in self.server.File._fields:
                    for method in self._file_methods:
                        if field in self._file_methods[method]:
                            if getattr(self, method, False):
                                call_values.append(getattr(self, method)(hash, i))
                            else:
                                calls.append({'methodName': method, 'params': [hash, i]})
                            break

        multicall_values = [value[0] for value in self._rpc._multicall(calls)]

        files = {}
        for hash, file_count in hashes.items():
            files[hash] = []
            for i in range(file_count):
                file = self.server.File()
                for field in file._fields:
                    for method in self._file_methods:
                        if field in self._file_methods[method]:
                            setattr(file, field, call_values.pop(0) if getattr(self, method, False) else  multicall_values.pop(0))
                            break
                files[hash].append(file)

        return files.pop(0) if hash is type(str) else files

    @Action.required
    def get_properties(self, hash):
        hashes = [hash] if type(hash) is str else hash

        calls = []
        call_values = []
        for hash in hashes:
            for field in self.server.Properties._fields:
                for method in self._property_methods:
                    if field in self._property_methods[method]:
                        if getattr(self, method, False):
                            call_values.append(getattr(self, method)(hash))
                        else:
                            calls.append({'methodName': method, 'params': [hash]})
                        break

        multicall_values = [value[0] for value in self._rpc._multicall(calls)]

        properties = {}
        for hash in hashes:
            property = self.server.Properties()
            property.hash = hash

            for field in property._fields:
                for method in self._property_methods:
                    if field in self._property_methods[method]:
                        if getattr(self, method, False):
                            setattr(property, field, call_values.pop(0))
                        else:
                            setattr(property, field, multicall_values.pop(0))
                        break
            properties[hash] = property

        return properties.pop(0) if hash is type(str) else properties

    @Action.required
    def add_url(self, url):
        self._rpc.call('load', url, type(url) is list)

    @Action.optional
    def add_file(self, file):
        from xmlrpclib import Binary
        self._rpc.call('load_raw', Binary(file))

    @Action.required
    def start(self, hash):
        self._rpc.call('d.start', hash, type(hash) is list)

    @Action.required
    def stop(self, hash):
        self._rpc.call('d.close', hash, type(hash) is list)

    @Action.optional
    def pause(self, hash):
        self._rpc.call('d.stop', hash, type(hash) is list)

    @Action.optional
    def unpause(self, hash):
        self._rpc.call('d.resume', hash, type(hash) is list)

    @Action.optional
    def recheck(self, hash):
        self._rpc.call('d.check_hash', hash, type(hash) is list)

    @Action.required
    def remove(self, hash):
        self._rpc.call('d.erase', hash, type(hash) is list)

    @Action.optional
    def restart(self, hash):
        self.stop(hash)
        self.start(hash)


class Server(rTorrent, Server):

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
