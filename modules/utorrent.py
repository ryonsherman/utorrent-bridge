from lib.client import Client
from lib.server import Server


class uTorrent(object):

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

    # def get_transfers()


class Client(Client):

    _token = None

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

    def _request_http(self, string):
        string = "%s&token=%s" % (string, self._token)

        return super(Client, self)._request_http(string)


class Server(Server):

    _token_cache = []
    _response = {'build': uTorrent.BUILD}

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)

        self.add_route('/gui/', self.response_gui, True)
        self.add_route('/gui/token.html', self.response_token_html, True)

    def _write_cache(self):
        pass

    def _read_cache(self, cache_id):
        pass

    def response_default(self, *args, **kwargs):
        return "\ninvalid request"

    def response_token_html(self, *args, **kwargs):
        return "<html><div id='token' style='display:none;'>%s</div></html>" % self.get_token()

    def response_gui(self, *args, **kwargs):
        # TODO: Enable this after dev.
        # if not kwargs.get('token') or kwargs['token'] not in self._token_cache:
        #     return self.response_default()

        if kwargs.get('list'):
            self.get_transfers(cache_id=kwargs.get('cid'))

        action = kwargs.get('action')
        if action:
            method = 'action_%s' % action
            if hasattr(self, method):
                action = getattr(self, method)
                action(**kwargs)

        from json import dumps
        return dumps(self._response)

    def get_token(self):
        from uuid import uuid4 as generate_token

        token = str(generate_token())
        self._token_cache.append(token)

        return token

    def get_transfers(self, cache_id=None):
        self._response.update({
            'torrents': [],
            'torrentc': '12345678',
        })

        transfers = self.client.get_transfers()
        for transfer in transfers.values():
            torrent = []
            for detail in [
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
                ]:
                torrent.append(transfer.get(detail, 0))
            self._response['torrents'].append(torrent)

    def action_start(self, *args, **kwargs):
        self.client.action_start(kwargs.get('hash'))

    def action_stop(self, *args, **kwargs):
        self.client.action_stop(kwargs.get('hash'))
