import asyncio
import logging

from fastapi import FastAPI

from ..config import UplinkMonitorConfig
from .monitor import UplinkMonitor

logger = logging.getLogger(__name__)


async def init(app: FastAPI, config: UplinkMonitorConfig):
    uplink_monitor = UplinkMonitor(config)
    app.state.uplink_monitor = uplink_monitor
    app.state.uplink_monitor_task = asyncio.create_task(uplink_monitor.run())

    logger.info('Started UplinkMonitor')

async def close(app: FastAPI):
    app.state.uplink_monitor_task.cancel()
    try:
        await app.state.uplink_monitor_task
    except asyncio.CancelledError:
        # Task cancellation is expected here as we've called cancel()
        pass

    logger.info('Stopped UplinkMonitor')