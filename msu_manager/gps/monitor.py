import asyncio
import logging
import time

from gpsd_client_async import GpsdClient, TpvMessage
from gpsd_client_async.messages import Mode
from prometheus_client import Summary

from ..command import run_command
from ..config import GpsConfig
from .types import Position

logger = logging.getLogger(__name__)

GPS_MEASUREMENT_INTERVAL_SUMMARY = Summary('gps_measurement_interval', 'Tracks intervals between GPS measurements')


class GpsMonitor:

    def __init__(self, config: GpsConfig):
        self._config = config
        self._gpsd_client = GpsdClient(host=self._config.gpsd_host, port=self._config.gpsd_port)
        self._latest_tpv_msg: TpvMessage = None
        self._inferred_measurement_rate_ms = 0
        
    async def run(self):
        while True:
            try:
                if self._config.init_cmd is not None:
                    await self._init_gps()

                async with self._gpsd_client as client:
                    previous_msg_time = time.time()

                    async for message in client:
                        if isinstance(message, TpvMessage):
                            self._latest_tpv_msg = message

                            current_time = time.time()
                            GPS_MEASUREMENT_INTERVAL_SUMMARY.observe(current_time - previous_msg_time)
                            previous_msg_time = current_time
            except asyncio.CancelledError:
                logger.debug('GpsMonitor task cancelled.')
                raise
            except (ConnectionError, IOError, Exception):
                logger.debug(f'Error in gpsd monitor', exc_info=True)
                self._latest_tpv_msg = None
                await asyncio.sleep(2)

    async def _init_gps(self) -> None:
        logger.info(f'Initializing GPS device (running {' '.join(self._config.init_cmd)})')

        retcode, stdout, stderr = await run_command(self._config.init_cmd)
        if retcode != 0:
            logger.error(f'GPS init command {' '.join(self._config.init_cmd)} failed with code {retcode}')
            logger.error(f'STDOUT: {stdout}')
            logger.error(f'STDERR: {stderr}')
            raise IOError('Count not initialize GPS device')

    @property
    def position(self):
        if self._latest_tpv_msg is None or self._latest_tpv_msg.mode not in (Mode.fix2D, Mode.fix3D):
            return Position(lat=0, lon=0, fix=False)
        
        return Position(
            lat=self._latest_tpv_msg.lat,
            lon=self._latest_tpv_msg.lon,
            fix=True,
        )
