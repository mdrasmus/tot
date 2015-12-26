import socket

from tot.config import get_user
from tot.config import Session


class Tracer(object):
    def __init__(self, session=None):
        self.retcode = None
        self.session = session or Session()

    def trace(self, cmd):
        return iter([])
