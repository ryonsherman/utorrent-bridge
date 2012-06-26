from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler


class Server(object):

    class Handler(SimpleHTTPRequestHandler):
        _routes = {}

        def _response_auth(self):
            self.send_response(401)
            self.send_header("WWW-Authenticate", "Basic realm=\"uTorrent Bridge\"")
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def _response_default(self, response=None):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(response)

        def _auth_basic(self):
            header = self.headers.getheader('Authorization')
            if header:
                from base64 import b64decode

                username, password = b64decode(header.split(' ')[-1]).split(':')

                if username == self.username and password == self.password:
                    return True

            return False

        def do_GET(self):
            path = self.path.split('?')
            route = self._routes.get(path[0], self._routes['/'])

            args = dict([arg.split('=') for arg in path[1].split('&')]) if len(path) > 1 else {}

            if route['auth']:
                auth = getattr(self, "_auth_%s" % self.auth)
                if not auth():
                    return self._response_auth()

            self._response_default(route['callback'](**args))

    def __init__(self, *args, **kwargs):
        self.address = kwargs['address']
        self.port = int(kwargs['port'])

        self.handler = self.Handler
        self.handler.auth = kwargs['auth']
        self.handler.username = kwargs.get('username')
        self.handler.password = kwargs.get('password')

        self.server = HTTPServer((self.address, self.port), self.handler)

        self.add_route('/', self.response_default)

    @property
    def routes(self):
        return self.server.RequestHandlerClass._routes

    def start(self):
        self.server.serve_forever()

    def stop(self):
        self.server.server_close()

    def add_route(self, path, callback, auth=False):
        self.routes[path] = {'callback': callback, 'auth': auth}

    def response_default(self, *args, **kwargs):
        return "<html></html>"
