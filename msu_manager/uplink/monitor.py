import asyncio
import logging

from ..config import ModemType, UplinkMonitorConfig
from .modem import TCL_IKE41VE1, DummyModem
from .status import Ping, Throughput

logger = logging.getLogger(__name__)


class UplinkMonitor:
    def __init__(self, config: UplinkMonitorConfig):
        self._config = config
        self._check_interval_s = config.check_interval_s
        self._ping = Ping(config.ping, interface=config.wwan_interface)
        self._throughput = Throughput(interface=config.wwan_interface)
        self._modem = None
        self._setup_modem()

        self._is_up = False

    def _setup_modem(self) -> None:
        if self._config.modem.type == ModemType.DUMMY:
            self._modem = DummyModem()
        elif self._config.modem.type == ModemType.TCL_IKE41VE1:
            self._modem = TCL_IKE41VE1(
                ping=self._ping,
                apn=self._config.wwan_apn,
                wwan_iface=self._config.wwan_interface,
                reboot_enabled=self._config.modem.reboot_enabled,
                reboot_threshold_s=self._config.modem.reboot_threshold_s,
            )

    @property
    def is_up(self):
        return self._is_up

    async def run(self):
        try:
            while True:
                if not await self._check_connection():
                    logger.warning("Connection is down, attempting to restore...")
                    await self._modem.reconnect()
                    success = await self._check_connection()
                    if success:
                        logger.info("Connection restored successfully.")
                    else:
                        logger.error("Failed to restore connection.")
                logger.debug(f'Connection status: {"up" if self._is_up else "down"}')
                await asyncio.sleep(self._check_interval_s)
        except asyncio.CancelledError:
            logger.info("UplinkMonitor task cancelled.")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred in UplinkMonitor", exc_info=True)

    async def _check_connection(self) -> bool:
        result = await self._throughput.check() or await self._ping.check()
        self._is_up = result
        return result