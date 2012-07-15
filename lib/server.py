from lib import Interface
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


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

        def _scrub_args(self, args):
            from urllib2 import unquote

            for key, value in args.items():
                if type(value) is list:
                    scrubbed_args = []
                    for value in value:
                        scrubbed_args.append(unquote(value))
                    args[key] = scrubbed_args
                else:
                    args[key] = unquote(value)

            return args

        @property
        def route(self):
            return self._routes.get(self.path.split('?')[0], self._routes['/'])

        @property
        def args(self):
            self._args = getattr(self, '_args', {})

            path = self.path.split('?')
            if len(path) > 1 and not self._args:
                from cgi import parse_qs
                for key, value in self._scrub_args(parse_qs(path[1])).items():
                    self._args[key] = value[0] if type(value) is list and len(value) is 1 else value

            return self._args

        @args.setter
        def args(self, args):
            self._args = args

        def authorize(self):
            if self.route['auth']:
                method = '_auth_%s' % self.auth
                if hasattr(self, method):
                    auth = getattr(self, method)
                    if auth and not auth():
                        self._response_auth()
                        return False
            return True

        def do_GET(self):
            if not self.authorize():
                return

            self._response_default(self.route['callback'](**self.args))

        def do_POST(self):
            if not self.authorize():
                return

            from cgi import parse_header, parse_multipart

            content_type, params = parse_header(self.headers.getheader('content-type'))
            if content_type == 'multipart/form-data':
                for key, value in parse_multipart(self.rfile, params).items():
                    self.args[key] = value[0] if type(value) is list and len(value) is 1 else value

            self._response_default(self.route['callback'](**self.args))

        def log_message(self, format, *args):
            message = "%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args)

            if self.log:
                open(self.log, 'a+b').write(message)

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
