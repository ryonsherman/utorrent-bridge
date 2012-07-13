class Action(object):

    @classmethod
    def required(self, method):
        method.action_required = True
        return method

    @classmethod
    def optional(self, method):
        method.action_required = False
        return method


class Interface(object):

    @Action.required
    def get_transfers(self):
        raise NotImplementedError

    # @action
    # def add_file(self):

    @Action.required
    def add_url(self, url):
        raise NotImplementedError

    @Action.required
    def start(self, hash):
        raise NotImplementedError

    @Action.required
    def stop(self, hash):
        raise NotImplementedError

    @Action.required
    def remove(self, hash):
        raise NotImplementedError
