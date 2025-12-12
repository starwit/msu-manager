import asyncio
import logging

from fastapi import APIRouter, status

from ..config import GpsConfig
from .monitor import GpsMonitor

logger = logging.getLogger(__name__)


class GpsSkill:
    def __init__(self, config: GpsConfig):
        self._config = config
        self._gps_monitor = None
        self._monitor_task = None

    async def run(self) -> None:
        self._gps_monitor = GpsMonitor(self._config)
        self._monitor_task = asyncio.create_task(self._gps_monitor.run())

        logger.info('Started GPS monitor')

    async def close(self) -> None:
        self._monitor_task.cancel()
        try:
            await self._monitor_task
        except asyncio.CancelledError:
            # Task cancellation is expected here as we've called cancel()
            pass

        logger.info('Stopped GpsSkill')

    def add_routes(self, router: APIRouter) -> None:

        @router.get('/position', status_code=status.HTTP_200_OK)
        async def position_endpoint():
            return {'status': 'UP' if self._gps_monitor.is_up else 'DOWN'}