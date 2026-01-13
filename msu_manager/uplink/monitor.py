import asyncio
import logging

from ..command import run_command
from ..config import UplinkMonitorConfig
from .modem import TCL_IKE41VE1
from .ping import Ping

logger = logging.getLogger(__name__)

class UplinkMonitor:
    def __init__(self, config: UplinkMonitorConfig):
        self._restore_connection_cmd = config.restore_connection_cmd
        self._restore_connection_env = {
            'WWAN_IFACE': config.wwan_device,
            'APN': config.wwan_apn,
        }
        self._check_interval_s = config.check_interval_s
        self._is_up = False
        self._ping = Ping(config.ping)
        self._modem = TCL_IKE41VE1()

    @property
    def is_up(self):
        return self._is_up

    async def run(self):
        try:
            while True:
                self._is_up = await self._ping.check()
                logger.debug(f'Connection status: {"up" if self._is_up else "down"}')
                if not self._is_up:
                    logger.warning("Connection is down, attempting to restore...")
                    success = await self.restore_connection()
                    if success:
                        logger.info("Connection restored successfully.")
                    else:
                        logger.error("Failed to restore connection.")
                await asyncio.sleep(self._check_interval_s)
        except asyncio.CancelledError:
            logger.info("UplinkMonitor task cancelled.")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred in UplinkMonitor", exc_info=True)
