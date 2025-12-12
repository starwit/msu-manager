import asyncio
import logging
import time
from typing import List

from prometheus_client import Enum, Gauge, Summary

from .messages import (HcuMessage, HeartbeatCommand, LogCommand, ResumeCommand,
                       ShutdownCommand)

logger = logging.getLogger(__name__)

TIME_SINCE_LAST_HEARTBEAT_SUMMARY = Summary('hcu_time_since_last_heartbeat', 'Tracks time intervals between HCU heartbeats')
NUMERIC_LOG_GAUGE = Gauge('hcu_log', 'Tracks numeric HCU log event values', ['key'])
IGNITION_STATE_ENUM = Enum('hcu_ignition_state', 'Ignition state of the vehicle as reported by the HCU', states=['on', 'off', 'unknown'])


class HcuController:
    def __init__(self, shutdown_command: List[str], shutdown_delay_s: int):
        self.shutdown_command = shutdown_command
        self.shutdown_delay_s = shutdown_delay_s
        self._shutdown_task = None
        self._last_heartbeat_time = time.time()
        IGNITION_STATE_ENUM.state('unknown')

    async def process_command(self, command: HcuMessage):
        logger.info(f'Processing {type(command).__name__}')
        match command:
            case ShutdownCommand():
                await self.handle_shutdown()
            case ResumeCommand():
                await self.handle_resume()
            case HeartbeatCommand():
                self._handle_heartbeat()
            case LogCommand():
                self._handle_log(command)
                
    async def handle_shutdown(self):
        IGNITION_STATE_ENUM.state('off')

        if self._shutdown_task is not None:
            logger.warning('Shutdown already scheduled, ignoring duplicate request.')
            return
        
        logger.info(f'Scheduling shutdown in {self.shutdown_delay_s} seconds.')
        self._shutdown_task = asyncio.create_task(self._delayed_shutdown())

    async def handle_resume(self):
        IGNITION_STATE_ENUM.state('on')
        
        if self._shutdown_task is None:
            logger.warning('No shutdown scheduled, nothing to resume.')
            return
        
        logger.info('Cancelling scheduled shutdown.')
        await self._cancel_shutdown()
        logger.info('Scheduled shutdown cancelled successfully.')

    async def _cancel_shutdown(self):
        if self._shutdown_task is not None:
            self._shutdown_task.cancel()
            try:
                await self._shutdown_task
            except asyncio.CancelledError:
                # Task cancellation is expected here as we've called cancel()
                pass
            self._shutdown_task = None
        
    async def _delayed_shutdown(self):
        await asyncio.sleep(self.shutdown_delay_s)
        
        logger.info('Executing shutdown now.')
        proc = await asyncio.create_subprocess_exec(*self.shutdown_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()

        # This is probably never reached if shutdown is successful
        if proc.returncode != 0:
            logger.error(f'Shutdown command failed with exit code {proc.returncode}')
            if stdout:
                logger.error(f'[stdout]\n{stdout.decode()}')
            if stderr:
                logger.error(f'[stderr]\n{stderr.decode()}')
            await self._cancel_shutdown()

    def _handle_heartbeat(self):
        current_time = time.time()
        TIME_SINCE_LAST_HEARTBEAT_SUMMARY.observe(current_time - self._last_heartbeat_time)
        self._last_heartbeat_time = current_time        

    def _handle_log(self, command: LogCommand):
        logger.info(f'LOG - {command.key}: {command.value}')
        if self._is_number(command.value):
            NUMERIC_LOG_GAUGE.labels(command.key).set(float(command.value))
        
    def _is_number(self, value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False