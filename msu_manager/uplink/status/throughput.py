import asyncio
import logging
import time
from functools import partial

import psutil
from prometheus_client import Summary
from psutil._ntuples import snetio

BYTES_RECEIVED_SUMMARY = Summary('uplink_bytes_received', 'Bytes received on given network interface')

logger = logging.getLogger(__name__)


class Throughput:

    def __init__(self, interface: str, staleness_threshold_s: float):
        self._interface = interface
        self._previous_bytes_received = 0
        self._last_check_time = time.time()
        self._staleness_threshold_s = staleness_threshold_s
        # Trigger check once s.t. we get a current counter value
        asyncio.create_task(self.check())
        
    async def check(self) -> bool:
        counters = await self._get_counters()
        if self._interface not in counters:
            return False
        
        bytes_received = counters[self._interface].bytes_recv
        BYTES_RECEIVED_SUMMARY.observe(bytes_received)
        is_bytes_increased = self._previous_bytes_received != bytes_received
        self._previous_bytes_received = bytes_received

        elapsed_time = time.time() - self._last_check_time
        if elapsed_time > self._staleness_threshold_s:
            logger.warning(f'Throughput has not been checked since {round(elapsed_time, 2)}s')

        self._last_check_time = time.time()
        
        return is_bytes_increased
    
    async def _get_counters(self) -> dict[str, snetio]:
        return await asyncio.get_running_loop().run_in_executor(None, partial(psutil.net_io_counters, pernic=True))