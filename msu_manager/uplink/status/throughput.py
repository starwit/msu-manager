import asyncio
import logging
from functools import partial

import psutil
from prometheus_client import Gauge
from psutil._ntuples import snetio

BYTES_RECEIVED_GAUGE = Gauge('uplink_bytes_received', 'Bytes received on configured uplink network interface')

logger = logging.getLogger(__name__)


class Throughput:

    def __init__(self, interface: str):
        self._interface = interface
        self._previous_bytes_received = 0
        # Trigger check once s.t. we get a current counter value
        asyncio.create_task(self.check())
        
    async def check(self) -> bool:
        counters = await self._get_counters()
        if self._interface not in counters:
            return False
        
        bytes_received = counters[self._interface].bytes_recv
        BYTES_RECEIVED_GAUGE.set(bytes_received)
        # The counter may also be smaller in case the OS resets it to 0, so we're looking for any difference
        is_counter_increased = self._previous_bytes_received != bytes_received
        self._previous_bytes_received = bytes_received

        return is_counter_increased
    
    async def _get_counters(self) -> dict[str, snetio]:
        return await asyncio.get_running_loop().run_in_executor(None, partial(psutil.net_io_counters, pernic=True))