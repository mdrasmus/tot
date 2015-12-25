import socket

from tot.config import get_user


class Tracer(object):
    def __init__(self, host=None):
        self.retcode = None
        self.host = host or socket.gethostname()
        self.user = get_user()

    def trace(self, cmd):
        return iter([])
