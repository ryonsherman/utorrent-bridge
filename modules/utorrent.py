from __future__ import division

from lib.client import Client
from lib.server import Server


class Transfer:
    _fields = [
        'hash',
        'status',
        'name',
        'size',
        'percent_progress',
        'downloaded',
        'uploaded',
        'ratio',
        'upload_speed',
        'download_speed',
        'eta',
        'label',
        'peers_connected',
        'peers_in_swarm',
        'seeds_connected',
        'seeds_in_swarm',
        'availability',
        'torrent_queue_order',
        'remaining'
    ]

    hash = ''
    status = 0
    name = ''
    size = 0
    downloaded = 0
    uploaded = 0
    ratio = 0
    upload_speed = 0
    download_speed = 0
    eta = 0
    label = ''
    peers_connected = 0
    peers_in_swarm = 0
    seeds_connected = 0
    seeds_in_swarm = 0
    availability = 0
    torrent_queue_order = 0
    remaining = 0

    @property
    def percent_progress(self):
        return int(self.downloaded / self.size * 1000) if self.size else 0


class uTorrent:

    BUILD = 27220

    class BOOLEAN:
        DISABLED = -1
        FALSE = 0
        TRUE = 1

    class DATA_TYPE:
        INTEGER = 0
        BOOLEAN = 1
        STRING = 2

    class STATUS:
        STARTED = 1
        CHECKING = 2
        CHECK_START = 4
        CHECKED = 8
        ERROR = 16
        PAUSED = 32
        QUEUED = 64
        LOADED = 128

    class PRIORITY:
        EXCLUDE = 0
        LOW = 1
        NORMAL = 2
        HIGH = 3

    # def get_token()
    # def get_transfers()

    # def action_add_file()
    # def action_add_url()
    # def action_start()
    # def action_stop()
    # def action_forcestart()
    # def action_pause()
    # def action_unpause()
    # def action_restart()
    # def action_getfiles()
    # def action_getprops()
    # def action_getsettings()
    # def action_setsetting()
    # def action_recheck()
    # def action_removedata
    # def action_setprio()
    # def action_setprops()


class Client(uTorrent, Client):

    _token = None

    def _request_http(self, string):
        string = "%s&token=%s" % (string, self._token)

        return super(Client, self)._request_http(string)

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

        self._token = self.get_token()

    def get_token(self):
        response = super(Client, self)._request_http('/gui/token.html')
        if response:
            from xml.dom.minidom import parse

            dom = parse(response)
            response.close()

            token = dom.getElementsByTagName('div')[0].childNodes[0].data

            return token


class Server(uTorrent, Server):

    Transfer = Transfer
    _token_cache = []
    _response = {'build': uTorrent.BUILD}

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)

        self._add_route('/gui/', self.route_gui, True)
        self._add_route('/gui/token.html', self.route_token_html, True)

    def _write_cache(self, data):
        import os
        import pickle
        from datetime import datetime
        from tempfile import gettempdir

        path = "%s%sutorrent-bridge" % (gettempdir(), os.sep)
        if not os.path.exists(path):
            os.mkdir(path)

        cache_id = datetime.today().strftime('%Y%m%d%H%M%s')
        filename = "%s%s%s" % (path, os.sep, cache_id)

        file = open(filename, 'wb')
        pickle.dump(data, file)
        file.close()

        return cache_id

    def _read_cache(self, cache_id):
        import os
        from tempfile import gettempdir

        filename = "%s%sutorrent-bridge%s%s" % (gettempdir(), os.sep, os.sep, cache_id)
        if not os.path.exists(filename):
            return False

        import pickle
        file = open(filename, 'rb')
        data = pickle.load(file)
        file.close()

        # TODO: Should cache be removed after use?
        #os.remove(filename)

        return data

    def route_default(self, *args, **kwargs):
        return "\ninvalid request"

    def route_token_html(self, *args, **kwargs):
        return "<html><div id='token' style='display:none;'>%s</div></html>" % self.get_token()

    def route_gui(self, *args, **kwargs):
        if kwargs.get('token') and kwargs['token'] not in self._token_cache:
            return self.route_default()

        if kwargs.get('list'):
            self.get_transfers(cache_id=kwargs.get('cid'))

        action = kwargs.get('action')
        if action:
            method = 'action_%s' % action.replace('-', '_')
            if hasattr(self, method):
                action = getattr(self, method)
                action(**kwargs)

        import json
        return json.dumps(self._response)

    def get_token(self):
        from uuid import uuid4 as generate_token

        token = str(generate_token())
        self._token_cache.append(token)

        return token

    def get_transfers(self, cache_id=None):
        transfers = self.client.get_transfers()

        # TODO: Implement transfer labels
        self._response['label'] = []

        if cache_id:
            cache = self._read_cache(cache_id) or []

            self._response['torrentp'] = []
            for transfer in transfers:
                cached_transfer = filter(lambda cached_transfer: transfer.hash == cached_transfer.hash, cache)
                modified = filter(lambda field: getattr(transfer, field) != getattr(cached_transfer[0], field), self.Transfer._fields) if cached_transfer else False
                if not cached_transfer or modified:
                    self._response['torrentp'].append([getattr(transfer, field) for field in self.Transfer._fields])

            self._response['torrentm'] = []
            for cache_transfer in cache:
                if not filter(lambda transfer: cache_transfer.hash == transfer.hash, transfers):
                    self._response['torrentm'].append(cached_transfer.hash)
        else:
            self._response['torrents'] = []
            for transfer in transfers:
                self._response['torrents'].append([getattr(transfer, field) for field in self.Transfer._fields])

        self._response['torrentc'] = self._write_cache(transfers)

    def action_start(self, *args, **kwargs):
        self.client.action_start(kwargs.get('hash'))

    def action_stop(self, *args, **kwargs):
        self.client.action_stop(kwargs.get('hash'))

    def action_pause(self, *args, **kwargs):
        getattr(self.client, 'action_pause', self.client.action_stop)(kwargs.get('hash'))

    def action_unpause(self, *args, **kwargs):
        getattr(self.client, 'action_unpause', self.client.action_start)(kwargs.get('hash'))

    def action_recheck(self, *args, **kwargs):
        self.client.action_recheck(kwargs.get('hash'))

    def action_remove(self, *args, **kwargs):
        self.client.action_remove(kwargs.get('hash'))

    def action_removedata(self, *args, **kwargs):
        getattr(self.client, 'action_removedata', self.client.remove)(kwargs.get('hash'))

    def action_restart(self, *args, **kwargs):
        if not getattr(self.client, 'action_restart'):
            self.action_stop(*args, **kwargs)
            self.action_start(*args, **kwargs)
        else:
            self.client.action_restart(kwargs.get('hash'))

    def action_add_url(self, *args, **kwargs):
        self.client.action_add_url(kwargs.get('s'))
