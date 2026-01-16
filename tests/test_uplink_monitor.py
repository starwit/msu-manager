import asyncio
from unittest.mock import AsyncMock

import pytest

from msu_manager.config import (DummyModemConfig, PingConfig,
                                UplinkMonitorConfig)
from msu_manager.uplink.monitor import UplinkMonitor


@pytest.mark.asyncio
async def test_connection_transitioning_down_up():
    testee = UplinkMonitor(UplinkMonitorConfig(
        enabled=True,
        wwan_interface='wwan0',
        wwan_apn='internet',
        ping=PingConfig(target='8.8.8.8'),
        check_interval_s=0.1,
        modem=DummyModemConfig(),
    ))

    throughput_mock = AsyncMock()
    throughput_mock.check.return_value = False
    testee._throughput = throughput_mock

    ping_mock = AsyncMock()
    ping_mock.check.return_value = False
    testee._ping = ping_mock

    task = asyncio.create_task(testee.run())

    await asyncio.sleep(0.2)

    assert testee.is_up == False

    ping_mock.check.return_value = True

    await asyncio.sleep(0.2)

    assert testee.is_up == True

    task.cancel()
