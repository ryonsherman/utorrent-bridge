from lib.client import Client
from lib.server import Server


class Client(Client):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)


class Server(Server):

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
