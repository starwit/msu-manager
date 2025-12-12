import asyncio
from fastapi import APIRouter
from ..config import HcuControllerConfig
from .protocol import HcuProtocol
from .controller import HcuController
from .messages import HcuMessage
from fastapi import APIRouter, FastAPI, HTTPException, status

import logging

logger = logging.getLogger(__name__)


class HcuSkill:
    def __init__(self, config: HcuControllerConfig):
        self._config = config
        self._hcu_controller = None
        self._hcu_transport = None
        self._hcu_protocol = None

    async def run(self) -> None:
        self._hcu_controller = HcuController(self._config.shutdown_command, self._config.shutdown_delay_s)

        hcu_bind_address = self._config.udp_bind_address
        hcu_listen_port = self._config.udp_listen_port
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: HcuProtocol(controller=self._hcu_controller), local_addr=(hcu_bind_address, hcu_listen_port)
        )
        self._hcu_transport = transport
        self._hcu_protocol = protocol

        logger.info(f'Started HcuProtocol UDP listener on {hcu_bind_address}:{hcu_listen_port}')

    async def close(self):
        self._hcu_transport.close()

        logger.info('Stopped HcuProtocol UDP listener')

    def add_routes(self, router: APIRouter) -> None:

        @router.post('/command', status_code=status.HTTP_204_NO_CONTENT, responses={404: {}})
        async def command_endpoint(command: HcuMessage):
            logger.info(f'Received {type(command).__name__} via HTTP: {command.model_dump_json(indent=2)}')
            if not self._config.enabled:
                logger.warning('HcuController is disabled; ignoring command')
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='HcuController is disabled')

            await self._hcu_controller.process_command(command)