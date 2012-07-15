from lib import Interface
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urllib2 import unquote


class Server(Interface):

    class Handler(BaseHTTPRequestHandler):
        _routes = {}

        def _response_auth(self):
            self.send_response(401)
            self.send_header("WWW-Authenticate", "Basic realm=\"%s\"" % self.realm)
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

            args = {}
            if len(path) > 1:
                for field, value in [arg.split('=') for arg in path[1].split('&')]:
                    value = unquote(value)
                    if args.get(field):
                        if type(args[field]) != list:
                            args[field] = [args[field]]
                        args[field].append(value)
                    else:
                        args[field] = value

            if route['auth']:
                method = '_auth_%s' % self.auth
                if hasattr(self, method):
                    auth = getattr(self, method)
                    if auth and not auth():
                        return self._response_auth()

            self._response_default(route['callback'](**args))

        def log_message(self, format, *args):
            message = "%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args)

            if self.log:
                file = open(self.log, 'a+b')
                file.write(message)
                file.close()

            # TODO: Provide '-q, --quiet' option
            # import sys
            # sys.stderr.write(message)

    def __init__(self, *args, **kwargs):
        self.address = kwargs['address']
        self.port = int(kwargs['port'])

        handler = self.Handler
        handler.realm = kwargs.get('realm', "uTorrent Bridge")
        handler.auth = kwargs.get('auth')
        handler.username = kwargs.get('username')
        handler.password = kwargs.get('password')
        handler.log = kwargs.get('log')

        self._server = HTTPServer((self.address, self.port), handler)
        self._add_route('/', self.route_default)

    @property
    def _routes(self):
        return self._server.RequestHandlerClass._routes

    def _start(self):
        self._server.serve_forever()

    def _stop(self):
        self._server.server_close()

    def _add_route(self, path, callback, auth=False):
        self._routes[path] = {'callback': callback, 'auth': auth}

    def route_default(self, *args, **kwargs):
        return "<html></html>"
