from typing import Dict, List
import pytest
import asyncio
from unittest.mock import AsyncMock
from msu_manager.config import UplinkMonitorConfig, PingConfig
from msu_manager.uplink.monitor import UplinkMonitor

@pytest.fixture
def uplink_monitor():
    """Create a UplinkMonitor instance for testing."""
    return UplinkMonitor(
        config=UplinkMonitorConfig(
            enabled=True,
            restore_connection_cmd=['./restore'],
            wwan_device='test_wwan',
            wwan_apn='test_apn',
            ping=PingConfig(target='8.8.8.8'),
            check_interval_s=5
        )
    )

def create_mock_process(returncode, stdout=b'', stderr=b''):
    """Helper function to create a mock subprocess."""
    mock_process = AsyncMock()
    mock_process.returncode = returncode
    mock_process.communicate = AsyncMock(return_value=(stdout, stderr))
    return mock_process


def create_mock_sleep(iterations):
    """Helper function to create a mock sleep that cancels after N iterations."""
    sleep_count = 0
    async def mock_sleep(duration):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count >= iterations:
            raise asyncio.CancelledError()
    return mock_sleep


def create_mock_subprocess_sequence(ret_by_cmd: Dict[str, List[int]]):
    def side_effect(*args, **kwargs):
        cmd = args[0]
        remaining_ret = ret_by_cmd.get(cmd, None)
        assert remaining_ret is not None, f'Unexpected subprocess call: {cmd}'
        assert len(remaining_ret) > 0, f'Unexpected subprocess call: {cmd} (no calls left)'
        return create_mock_process(remaining_ret.pop(0))
    
    subprocess_mock = AsyncMock()
    subprocess_mock.side_effect = side_effect
    return subprocess_mock


@pytest.mark.asyncio
async def test_run_connection_up(uplink_monitor, monkeypatch):
    """Test run() when connection is always up."""
    # Three successful ping responses
    mock_subprocess = create_mock_subprocess_sequence({
        'ping': [0, 0, 0]
    })
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', mock_subprocess)
    
    # Run the check loop 3 times before cancelling
    monkeypatch.setattr(asyncio, 'sleep', create_mock_sleep(3))
    
    # Run the monitor
    with pytest.raises(asyncio.CancelledError):
        await uplink_monitor.run()
    
    # Verify that ping command was called
    assert mock_subprocess.call_count == 3

    # Verify that restore command was never called
    # (i.e., only ping commands were executed)
    assert all(call.args[0] == 'ping' for call in mock_subprocess.mock_calls)

@pytest.mark.asyncio
async def test_run_connection_down_restore_success(uplink_monitor, monkeypatch):
    """Test run() when connection goes down but restore succeeds."""
    # ping fails (1), restore succeeds (0), ping succeeds twice (0)
    mock_subprocess = create_mock_subprocess_sequence({
        'ping': [1, 0, 0],
        './restore': [0]
    })
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', mock_subprocess)
    
    monkeypatch.setattr(asyncio, 'sleep', create_mock_sleep(3))
    
    with pytest.raises(asyncio.CancelledError):
        await uplink_monitor.run()

    # Verify the sequence of commands executed
    assert [
        'ping',
        './restore',
        'ping',
        'ping'
    ] == [call.args[0] for call in mock_subprocess.mock_calls]

    # Verify that restore command was called with correct env (>= means "is superset of")
    assert mock_subprocess.mock_calls[1].kwargs['env'].items() >= {'WWAN_IFACE': 'test_wwan', 'APN': 'test_apn'}.items()
