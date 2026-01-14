from typing import Awaitable, Callable
from ..ping import Ping
import logging

logger = logging.getLogger(__name__)

class TCL_IKE41VE1:
    def __init__(self, ping: Ping):
        self._ping = ping

    def reconnect(self):
        logger.info('Reconnecting...')
