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

        @router.post('/message', status_code=status.HTTP_204_NO_CONTENT, responses={404: {'description': 'HcuController is disabled'}})
        async def message_endpoint(message: HcuMessage):
            logger.info(f'Received {type(message).__name__} via HTTP: {message.model_dump_json(indent=2)}')
            if not self._config.enabled:
                logger.warning('HcuController is disabled; ignoring message')
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='HcuController is disabled')

            await self._hcu_controller.process_message(message)

        @router.put('/shutdown/inhibit/{seconds}', status_code=status.HTTP_204_NO_CONTENT, responses={
            400: {'description': 'The inhibition time is invalid (either negative or exceeded the maximum value)'}
        })
        async def shutdown_inhibit_endpoint(seconds: int):
            if seconds < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Inhibition time cannot be negative')
            
            if seconds > self._config.shutdown_inhibit_max_s:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Inhibition time exceeds maximum of {self._config.shutdown_inhibit_max_s}s')
            
            logger.info(f'Inhibiting shutdown for {seconds}s per user request')
            await self._hcu_controller.inhibit_shutdown(seconds)

        @router.get('/shutdown/status')
        async def shutdown_status_endpoint():
            return {
                'shutdown_in_progress': self._hcu_controller.is_shutdown_scheduled,
                'remaining_runtime_s': self._hcu_controller.remaining_shutdown_time,
            }