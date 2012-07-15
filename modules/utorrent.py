from __future__ import division

from lib import Action, Interface
from lib.client import Client
from lib.server import Server


class uTorrent(Interface):

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

    def _get_token(self):
        raise NotImplementedError

    @Action.required
    def get_files(self, hash):
        raise NotImplementedError

    @Action.required
    def get_properties(self, hash):
        raise NotImplementedError

    @Action.optional
    def forcestart(self, hash):
        raise NotImplementedError

    @Action.optional
    def recheck(self, hash):
        raise NotImplementedError

    @Action.optional
    def removedata(self, hash):
        raise NotImplementedError

    # def action_getsettings()
    # def action_setsetting()
    # def action_setprio()
    # def action_setprops()


class Client(uTorrent, Client):

    _token = None

    def _request_http(self, string):
        string = "%s&token=%s" % (string, self._token)

        return super(Client, self)._request_http(string)

    def _get_token(self):
        response = super(Client, self)._request_http('/gui/token.html')
        if response:
            from xml.dom.minidom import parse

            dom = parse(response)
            response.close()

            token = dom.getElementsByTagName('div')[0].childNodes[0].data

            return token

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

        self._token = self.get_token()


class Transfer(object):
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
    status = uTorrent.STATUS.LOADED
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


class File(object):
    _fields = [
        'name',
        'size',
        'size_downloaded',
        'priority',
    ]

    name = ''
    size = 0
    size_downloaded = 0
    priority = 0


class Properties(object):
    _fields = [
        'hash',
        'trackers',
        'ulrate',
        'dlrate',
        'superseed',
        'dht',
        'pex',
        'seed_override',
        'seed_ratio',
        'seed_time',
        'ulslots'
    ]

    hash = ''
    trackers = ''
    ulrate = 0
    dlrate = 0
    superseed = 0
    dht = 0
    pex = 0
    seed_override = 0
    seed_ratio = 0
    seed_time = 0
    ulslots = 0


class Server(uTorrent, Server):

    Transfer = Transfer
    File = File
    Properties = Properties

    _token_cache = []
    _response = {'build': uTorrent.BUILD}
    _methods = {
        'get_files': ['getfiles'],
        'get_properties': ['getprops'],
    }

    def _get_token(self):
        from uuid import uuid4 as generate_token

        token = str(generate_token())
        self._token_cache.append(token)

        return token

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

        os.remove(filename)

        return data

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)

        self._add_route('/gui/', self.route_gui, True)
        self._add_route('/gui/token.html', self.route_token_html, True)

    def route_default(self, *args, **kwargs):
        return "\ninvalid request"

    def route_token_html(self, *args, **kwargs):
        return "<html><div id='token' style='display:none;'>%s</div></html>" % self._get_token()

    def route_gui(self, *args, **kwargs):
        if kwargs.get('token') and kwargs['token'] not in self._token_cache:
            return self.route_default()

        if kwargs.get('list'):
            self.get_transfers(cache_id=kwargs.get('cid'))

        action = kwargs.get('action')
        if action:
            del kwargs['action']
            action = action.replace('-', '_')
            for method in self._methods.keys():
                if action in self._methods[method]:
                    action = method
                    break
            if hasattr(self, action) and hasattr(getattr(self, action), 'action_required'):
                action = getattr(self, action)
                action(**kwargs)

        import json
        return json.dumps(self._response)

    @Action.required
    def get_transfers(self, cache_id=None):
        transfers = self.client.get_transfers()

        self._response = {'build': uTorrent.BUILD}

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

    @Action.required
    def get_files(self, *args, **kwargs):
        self._response = {'build': uTorrent.BUILD}

        self._response['files'] = []
        for hash, files in self.client.get_files(kwargs.get('hash')).items():
            self._response['files'].extend([hash, [[getattr(file, field) for field in self.File._fields] for file in files]])

    @Action.required
    def get_properties(self, *args, **kwargs):
        self._response = {'build': uTorrent.BUILD}

        self._response['props'] = []
        for hash, properties in self.client.get_properties(kwargs.get('hash')).items():
            self._response['props'].append(dict(zip(properties._fields, [getattr(properties, field) for field in properties._fields])))

    @Action.required
    def add_url(self, *args, **kwargs):
        self.client.add_url(kwargs.get('s'))

    @Action.optional
    def add_file(self, *args, **kwargs):
        self.client.add_file(kwargs.get('torrent_file'))

    @Action.required
    def start(self, *args, **kwargs):
        self.client.start(kwargs.get('hash'))

    @Action.required
    def stop(self, *args, **kwargs):
        self.client.stop(kwargs.get('hash'))

    @Action.optional
    def pause(self, *args, **kwargs):
        getattr(self.client, 'pause', self.client.stop)(kwargs.get('hash'))

    @Action.optional
    def unpause(self, *args, **kwargs):
        getattr(self.client, 'unpause', self.client.action_start)(kwargs.get('hash'))

    @Action.optional
    def recheck(self, *args, **kwargs):
        self.client.recheck(kwargs.get('hash'))

    @Action.required
    def remove(self, *args, **kwargs):
        self.client.remove(kwargs.get('hash'))

    @Action.optional
    def removedata(self, *args, **kwargs):
        getattr(self.client, 'removedata', self.client.remove)(kwargs.get('hash'))

    @Action.optional
    def restart(self, *args, **kwargs):
        if not getattr(self.client, 'restart'):
            self.stop(*args, **kwargs)
            self.start(*args, **kwargs)
        else:
            self.client.restart(kwargs.get('hash'))
