from lib.client import Client
from lib.server import Server


class uTorrent:

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

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)

    @property
    def token(self):
        from uuid import uuid4 as generate_token

        token = generate_token()
        self._token_cache.append(token)

        return token

    @property
    def token_html(self):
        return "<html><div id='token' style='display:none;'>%s</div></html>" % self.token
