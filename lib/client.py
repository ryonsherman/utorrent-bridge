class Client(object):

    def _request_http(self, string):
        from urllib2 import Request, urlopen

        url = "http://%s:%s/%s" % (self.address, self.port, string.lstrip('/'))
        self._request = Request(url)

        auth = getattr(self, "_auth_%s" % self.auth)
        if auth:
            auth()

        response = urlopen(self._request, None, 3)
        return response

    def _auth_basic(self):
        from base64 import encodestring

        header = "Basic %s" % encodestring("%s:%s" % (self.username, self.password))[:-1]
        self._request.add_header("Authorization", header)

    def __init__(self, *args, **kwargs):
        self.address = kwargs['address']
        self.port = kwargs['port']

        self.auth = kwargs.get('auth')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
