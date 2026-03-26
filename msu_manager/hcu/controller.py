import asyncio
import logging
import time
from typing import List

from prometheus_client import Enum, Gauge, Summary

from ..command import run_command
from .messages import (HcuMessage, HeartbeatMessage, LogMessage, MetricMessage,
                       ResumeMessage, ShutdownMessage)
from .shutdown import ShutdownError, ShutdownModel

logger = logging.getLogger(__name__)

TIME_SINCE_LAST_HEARTBEAT_SUMMARY = Summary('hcu_time_since_last_heartbeat', 'Tracks time intervals between HCU heartbeats')
METRIC_GAUGE = Gauge('hcu_metric', 'Tracks numeric HCU METRIC event values', ['key'])
IGNITION_STATE_ENUM = Enum('hcu_ignition_state', 'Ignition state of the vehicle as reported by the HCU', states=['on', 'off', 'unknown'])


class HcuController:
    def __init__(self, shutdown_command: List[str], shutdown_delay_s: int):
        self._shutdown_command = shutdown_command
        self._shutdown_task = None
        self._shutdown_task_execution_ts = None
        self._shutdown_model = ShutdownModel(shutdown_delay_s)
        self._last_heartbeat_time = time.time()
        IGNITION_STATE_ENUM.state('unknown')

    async def process_message(self, message: HcuMessage):
        logger.debug(f'Processing {type(message).__name__}')
        match message:
            case ShutdownMessage():
                await self.handle_shutdown()
            case ResumeMessage():
                await self.handle_resume()
            case HeartbeatMessage():
                self._handle_heartbeat()
            case LogMessage():
                self._handle_log(message)
            case MetricMessage():
                self._handle_metric(message)

    async def inhibit_shutdown(self, seconds: int):
        self._shutdown_model.inhibit(seconds)
        
        if self.is_shutdown_scheduled:
            await self._cancel_shutdown()
            await self._schedule_shutdown()

    @property
    def is_shutdown_scheduled(self) -> bool:
        return self._shutdown_task is not None

    @property
    def remaining_shutdown_time(self) -> float | None:
        try:
            time_remaining = self._shutdown_model.time_remaining
            return time_remaining if self.is_shutdown_scheduled else None
        except ShutdownError:
            return None
                
    async def handle_shutdown(self):
        IGNITION_STATE_ENUM.state('off')

        if self.is_shutdown_scheduled:
            logger.warning('Shutdown already scheduled, ignoring duplicate request.')
            return

        await self._schedule_shutdown()
        
    async def _schedule_shutdown(self):
        self._shutdown_model.start()
        time_remaining = self._shutdown_model.time_remaining

        if self._shutdown_model.is_inhibited:
            logger.info(f'Scheduling shutdown in {round(time_remaining, 2)} seconds (inhibited by user)')
        else:
            logger.info(f'Scheduling shutdown in {self._shutdown_model.static_delay} seconds.')
            
        self._shutdown_task = asyncio.create_task(self._delayed_shutdown(time_remaining))
        self._shutdown_task_execution_ts = time.time() + time_remaining

    async def handle_resume(self):
        IGNITION_STATE_ENUM.state('on')
        
        if not self.is_shutdown_scheduled:
            logger.warning('No shutdown scheduled, nothing to resume.')
            return
        
        logger.info('Cancelling scheduled shutdown.')
        await self._cancel_shutdown()
        logger.info('Scheduled shutdown cancelled successfully.')

    async def _cancel_shutdown(self):
        if self.is_shutdown_scheduled:
            self._shutdown_task.cancel()
            try:
                await self._shutdown_task
            except asyncio.CancelledError:
                # Task cancellation is expected here as we've called cancel()
                pass
            self._shutdown_task = None
            self._shutdown_task_execution_ts = None
            self._shutdown_model.stop()
        
    async def _delayed_shutdown(self, delay_s: int):
        await asyncio.sleep(delay_s)
        
        logger.info('Executing shutdown now.')
        retcode, stdout, stderr = await run_command(self._shutdown_command)

        # This is probably never reached if shutdown is successful
        if retcode != 0:
            logger.error(f'Shutdown command failed with exit code {retcode}')
            logger.error(f'[stdout]\n{stdout}')
            logger.error(f'[stderr]\n{stderr}')
            await self._cancel_shutdown()

        # Cleanup
        self._shutdown_task = None
        self._shutdown_task_execution_ts = None
        self._shutdown_model.stop()

    def _handle_heartbeat(self):
        current_time = time.time()
        TIME_SINCE_LAST_HEARTBEAT_SUMMARY.observe(current_time - self._last_heartbeat_time)
        self._last_heartbeat_time = current_time        

    def _handle_log(self, message: LogMessage):
        logger.debug(f'LOG - {message.level}: {message.message}')

    def _handle_metric(self, message: MetricMessage):
        logger.debug(f'METRIC - {message.key}: {message.value}')
        if self._is_number(message.value):
            METRIC_GAUGE.labels(message.key).set(float(message.value))
        
    def _is_number(self, value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False