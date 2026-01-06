import asyncio
import logging

import serial_asyncio
from fastapi import APIRouter, HTTPException, status

from ..config import HcuControllerConfig
from .controller import HcuController
from .messages import HcuMessage
from .protocol import HcuProtocol

logger = logging.getLogger(__name__)


class HcuSkill:
    def __init__(self, config: HcuControllerConfig):
        self._config = config
        self._hcu_controller = None
        self._hcu_transport = None
        self._hcu_protocol = None

    async def run(self) -> None:
        self._hcu_controller = HcuController(self._config.shutdown_command, self._config.shutdown_delay_s)

        loop = asyncio.get_running_loop()
        transport, protocol = await serial_asyncio.create_serial_connection(
            loop,
            lambda: HcuProtocol(controller=self._hcu_controller),
            str(self._config.serial_device.absolute()),
            baudrate=self._config.serial_baud_rate,
        )
        self._hcu_transport = transport
        self._hcu_protocol = protocol

        logger.info(f'Started HCU skill (on {self._config.serial_device.absolute()})')

    async def close(self):
        self._hcu_transport.close()

        logger.info('Stopped HCU skill')

    def add_routes(self, router: APIRouter) -> None:

        @router.post('/command', status_code=status.HTTP_204_NO_CONTENT, responses={404: {}})
        async def command_endpoint(command: HcuMessage):
            logger.info(f'Received {type(command).__name__} via HTTP: {command.model_dump_json(indent=2)}')
            if not self._config.enabled:
                logger.warning('HcuController is disabled; ignoring command')
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='HcuController is disabled')

            await self._hcu_controller.process_command(command)