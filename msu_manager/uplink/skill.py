import asyncio
import logging

from fastapi import APIRouter, status

from ..config import UplinkMonitorConfig
from .monitor import UplinkMonitor

logger = logging.getLogger(__name__)


class UplinkSkill:
    def __init__(self, config: UplinkMonitorConfig):
        self._config = config
        self._uplink_monitor = None
        self._monitor_task = None

    async def run(self) -> None:
        self._uplink_monitor = UplinkMonitor(self._config)
        self._monitor_task = asyncio.create_task(self._uplink_monitor.run())

        logger.info('Started UplinkMonitor')

    async def close(self) -> None:
        self._monitor_task.cancel()
        try:
            await self._monitor_task
        except asyncio.CancelledError:
            # Task cancellation is expected here as we've called cancel()
            pass

        logger.info('Stopped UplinkMonitor')

    def add_routes(self, router: APIRouter) -> None:

        @router.get('/status', status_code=status.HTTP_200_OK)
        async def status_endpoint():
            return {'status': 'UP' if self._uplink_monitor.is_up else 'DOWN'}