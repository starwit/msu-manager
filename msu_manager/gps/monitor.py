import asyncio
import logging
import time

from gpsd_client_async import GpsdClient, TpvMessage
from gpsd_client_async.messages import Mode

from ..config import GpsConfig
from .types import Position

logger = logging.getLogger(__name__)


class GpsMonitor:

    def __init__(self, config: GpsConfig):
        self._config = config
        self._gpsd_client = GpsdClient(host=self._config.gpsd_host, port=self._config.gpsd_port)
        self._latest_tpv_msg: TpvMessage = None
        self._inferred_measurement_rate_ms = 0
        
    async def run(self):
        while True:
            try:
                async with self._gpsd_client as client:
                    latest_msg_time = 0

                    async for message in client:
                        latest_msg_time = time.time()

                        if isinstance(message, TpvMessage):
                            self._latest_tpv_msg = message

            except asyncio.CancelledError:
                logger.debug('GpsMonitor task cancelled.')
                raise
            except (ConnectionError, Exception):
                logger.warning(f'Error in gpsd connection', exc_info=True)
                self._latest_tpv_msg = None
                await asyncio.sleep(2)

    @property
    def position(self):
        if self._latest_tpv_msg is None:
            return Position(lat=0, lon=0, fix=False)
        
        return Position(
            lat=self._latest_tpv_msg.lat,
            lon=self._latest_tpv_msg.lon,
            fix=self._latest_tpv_msg.mode in (Mode.fix2D, Mode.fix3D),
        )
