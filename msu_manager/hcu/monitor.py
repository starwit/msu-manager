import asyncio
import logging

import serial_asyncio
from serial.serialutil import SerialException

from ..config import HcuControllerConfig
from .controller import HcuController
from .protocol import HcuProtocol

logger = logging.getLogger(__name__)


class HcuMonitor:
    def __init__(self, config: HcuControllerConfig, controller: HcuController):
        self._config = config
        self._hcu_controller = controller
        self._hcu_protocol = None

    async def run(self) -> None:
        while True:
            try:
                if self._hcu_protocol is None or not self._hcu_protocol.is_connected:
                    await self._init_serial()
            except SerialException as e:
                logger.warning(f'Serial connection error: {e}')
            except:
                logger.warning(f'Unexpected exception in HCU skill main loop', exc_info=True)
            finally:
                await asyncio.sleep(2)

    async def _init_serial(self) -> None:
        if self._hcu_protocol is not None:
            self._hcu_protocol.close()
            self._hcu_protocol = None

        loop = asyncio.get_running_loop()
        _, protocol = await serial_asyncio.create_serial_connection(
            loop,
            lambda: HcuProtocol(controller=self._hcu_controller),
            str(self._config.serial_device.absolute()),
            baudrate=self._config.serial_baud_rate,
        )
        self._hcu_protocol = protocol
    
        logger.info(f'Initialized serial port ({self._config.serial_device})')

    async def close(self):
        self._hcu_protocol.close()