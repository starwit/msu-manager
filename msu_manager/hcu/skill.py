import asyncio
import logging

from fastapi import APIRouter, HTTPException, status

from ..config import HcuControllerConfig
from .controller import HcuController
from .messages import HcuMessage
from .monitor import HcuMonitor

logger = logging.getLogger(__name__)


class HcuSkill:
    def __init__(self, config: HcuControllerConfig):
        self._config = config
        self._hcu_controller = None
        self._hcu_monitor = None
        self._monitor_task = None

    async def run(self) -> None:
        self._hcu_controller = HcuController(self._config.shutdown_command, self._config.shutdown_delay_s)
        self._hcu_monitor = HcuMonitor(self._config, self._hcu_controller)
        self._monitor_task = asyncio.create_task(self._hcu_monitor.run())

        logger.info(f'Started HCU skill')

    async def close(self):
        self._monitor_task.cancel()
        try:
            await self._monitor_task
        except asyncio.CancelledError:
            # Task cancellation is expected during shutdown; suppress the exception.
            pass

        logger.info('Stopped HCU skill')

    def add_routes(self, router: APIRouter) -> None:

        @router.post('/command', status_code=status.HTTP_204_NO_CONTENT, responses={404: {}})
        async def command_endpoint(command: HcuMessage):
            logger.info(f'Received {type(command).__name__} via HTTP: {command.model_dump_json(indent=2)}')
            if not self._config.enabled:
                logger.warning('HcuController is disabled; ignoring command')
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='HcuController is disabled')

            await self._hcu_controller.process_command(command)