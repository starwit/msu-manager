from msu_manager.uplink.status import Throughput, Ping
from msu_manager.config import PingConfig
import pytest

@pytest.mark.asyncio
async def test_throughput_on_localhost():
    localhost_ping = Ping(PingConfig(target='127.0.0.1', interface='lo'))

    testee = Throughput(interface='lo', staleness_threshold_s=10)

    # Ping once to make sure the interface bytes counter changes
    await localhost_ping.check()

    assert await testee.check() == True

@pytest.mark.asyncio
async def test_throughput_non_existing_if():
    testee = Throughput(interface='DOES_NOT_EXIST', staleness_threshold_s=10)

    assert await testee.check() == False