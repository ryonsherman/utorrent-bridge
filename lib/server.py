from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler


class Server(object):

    class Handler(SimpleHTTPRequestHandler):
        _routes = {}

        def _return_auth(self):
            self.send_response(401)
            self.send_header("WWW-Authenticate", "Basic realm=\"uTorrent Bridge\"")
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def _return_success(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def _auth_basic(self):
            header = self.headers.getheader('Authorization')
            if header:
                from base64 import b64decode

                username, password = b64decode(header.split(' ')[-1]).split(':')

                if username == self.username and password == self.password:
                    return True

            return False

        def do_GET(self):
            auth = getattr(self, "_auth_%s" % self.auth)
            self._return_success() if auth() else self._return_auth()

            route = self._routes.get(self.path)
            self.wfile.write(route() if route else self._routes['/']())

    def __init__(self, *args, **kwargs):
        self.address = kwargs['address']
        self.port = int(kwargs['port'])

        self.handler = self.Handler
        self.handler.auth = kwargs['auth']
        self.handler.username = kwargs.get('username')
        self.handler.password = kwargs.get('password')

        self.server = HTTPServer((self.address, self.port), self.handler)

        self.routes['/'] = self.route_default

    @property
    def routes(self):
        return self.server.RequestHandlerClass._routes

    def start(self):
        self.server.serve_forever()

    def stop(self):
        self.server.server_close()

    def add_route(self, route, callback):
        self.server.RequestHandlerClass._routes[route] = callback

    def route_default(self):
        return "<html></html>"
