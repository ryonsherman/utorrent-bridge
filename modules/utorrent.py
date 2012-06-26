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


class Client(Client):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)


class Server(Server):

    _token_cache = []
    _response = {'build': uTorrent.BUILD}

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)

        self.add_route('/gui/', self.response_gui, True)
        self.add_route('/gui/token.html', self.response_token_html)

    @property
    def token(self):
        from uuid import uuid4 as generate_token

        token = str(generate_token())
        self._token_cache.append(token)

        return token

    def response_default(self, *args, **kwargs):
        return "\ninvalid request"

    def response_token_html(self, *args, **kwargs):
        return "<html><div id='token' style='display:none;'>%s</div></html>" % self.token

    def response_gui(self, *args, **kwargs):
        if not kwargs.get('token') or kwargs['token'] not in self._token_cache:
            return self.response_default()

        from json import dumps

        return dumps(self._response)
