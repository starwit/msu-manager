import logging
import re
from typing import NamedTuple

from prometheus_client import Histogram

from ...command import run_command
from ...config import PingConfig

PING_ROUNDTRIP_HISTOGRAM = Histogram('uplink_ping_roundtrip', 'Roundtrip time in milliseconds as reported by ping',
                                     buckets=(5, 10, 25, 50, 75, 100, 250, 500, 750))


logger = logging.getLogger(__name__)


class PingResult(NamedTuple):
    packets_transmitted: int
    packets_received: int
    rtt_min: float
    rtt_avg: float
    rtt_max: float
    rtt_mdev: float


class Ping:
    def __init__(self, config: PingConfig, interface: str = None):
        self._ping_cmd = [
            'ping',
            '-n',
            '-c', str(config.count),
            '-w', str(config.deadline_s),
            '-i', str(config.interval_s),
            *(['-I', interface] if interface else []),
            config.target,
        ]

    async def check(self) -> bool:
        _, stdout, stderr = await run_command(self._ping_cmd, {'LC_ALL': 'C'})
        
        result = self._parse_ping_output(stdout)
        if result is None:
            logger.error(f'Parsing ping output failed ({" ".join(self._ping_cmd)})')
            logger.error(f"STDOUT:")
            logger.error(f"{stdout}")
            logger.error(f"STDERR:")
            logger.error(f"{stderr}")
            return False
        
        if result.packets_received == 0:
            return False
        else:
            PING_ROUNDTRIP_HISTOGRAM.observe(result.rtt_avg)
            return True

    def _parse_ping_output(self, output: str) -> PingResult | None:
        # Parse packet statistics: "2 packets transmitted, 2 received, ..."
        packets_match = re.search(r'(\d+)\s+packets transmitted,\s+(\d+)\s+received', output)
        if not packets_match:
            return None
        
        packets_transmitted = int(packets_match.group(1))
        packets_received = int(packets_match.group(2))
        
        # Parse RTT statistics (optional): "rtt min/avg/max/mdev = 10.960/12.434/13.909/1.474 ms"
        rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
        if rtt_match:
            rtt_min = float(rtt_match.group(1))
            rtt_avg = float(rtt_match.group(2))
            rtt_max = float(rtt_match.group(3))
            rtt_mdev = float(rtt_match.group(4))
        else:
            rtt_min = rtt_avg = rtt_max = rtt_mdev = 0.0
        
        return PingResult(
            packets_transmitted=packets_transmitted,
            packets_received=packets_received,
            rtt_min=rtt_min,
            rtt_avg=rtt_avg,
            rtt_max=rtt_max,
            rtt_mdev=rtt_mdev
        )