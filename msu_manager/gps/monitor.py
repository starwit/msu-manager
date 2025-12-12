import asyncio
from ..config import GpsConfig
from gpsd_client_async import GpsdClient


class GpsMonitor:

    def __init__(self, config: GpsConfig):
        self._config = config
        
    async def run(self):

        while True:
            asyncio.sleep(self._config.measurement_rate_ms / 1000)

    @property
    def position(self):
        pass

    async def close(self):
        pass