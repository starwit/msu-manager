from typing import Awaitable, Callable
from ..ping import Ping

class TCL_IKE41VE1:
    def __init__(self, ping: Ping):
        self._ping = ping

    def reconnect(self):
        pass
