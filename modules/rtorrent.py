from lib.client import Client
from lib.server import Server


class Client(Client):

    class RPC(object):

        def __init__(self):
            pass

        def call(self):
            pass

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

        from xmlrpclib import Server
        url = "http://%s:%s/RPC2" % (self.address, self.port)
        self._rpc = Server(url)

    def get_transfers(self, views=['main']):
        hashes = self._rpc.download_list(views)

        calls = []
        for hash in hashes:
            calls.append({'methodName': 'd.get_tracker_size', 'params': [hash]})
        # tracker_sizes = self._rpc.system.multicall(calls)

        calls = []
        for index, hash in enumerate(hashes):
            for method in [
                'd.is_active',
                'd.get_name',
                'd.get_size_bytes',
                'd.get_completed_bytes',
                'd.get_up_total',
                'd.get_ratio',
                'd.get_up_rate',
                'd.get_down_rate',
                'd.get_peers_accounted',
                'd.get_peers_complete',
                'd.get_left_bytes'
                ]:
                calls.append({'methodName': method, 'params': [hash]})

        details = self._rpc.system.multicall(calls)

        cursor = 0
        transfers = {}
        for hash in hashes:
            transfer = {}
            transfer['hash'] = hash

            for detail in [
                'status',
                'name',
                'size',
                'downloaded',
                'uploaded',
                'ratio',
                'upload_speed',
                'download_speed',
                'peers_connected',
                'seeds_connected',
                'remaining'
                ]:
                transfer[detail] = details[cursor][0]
                cursor += 1

            transfers[hash] = transfer

        return transfers

    def action_start(self, hash):
        self._rpc.d.start(hash)

    def action_stop(self, hash):
        self._rpc.d.stop(hash)


class Server(Server):

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
