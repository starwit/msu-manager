import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from msu_manager.config import HcuControllerConfig
from msu_manager.hcu.skill import HcuSkill


@pytest_asyncio.fixture
async def write_serial_input(unused_tcp_port):
    dummy_writer = None

    def connect_cb(_, writer):
        nonlocal dummy_writer
        dummy_writer = writer
    
    await asyncio.start_server(connect_cb, '127.0.0.1', unused_tcp_port)

    async def writer(data: bytes):
        dummy_writer.write(data)
        await dummy_writer.drain()

    return writer

@pytest.fixture
def serial_device_path_mock(unused_tcp_port):
    serial_socket_url = f'socket://127.0.0.1:{unused_tcp_port}'

    serial_device_path_mock = MagicMock(wraps=Path, spec=Path)
    serial_device_path_mock.__str__.return_value = serial_socket_url
    serial_device_path_mock.absolute.return_value = serial_socket_url

    return serial_device_path_mock

@pytest.mark.asyncio
async def test_shutdown(tmp_path, serial_device_path_mock, write_serial_input):
    tmp_file = tmp_path / 'shutdown_executed'

    hcu_skill = HcuSkill(HcuControllerConfig(
        enabled=True,
        serial_device=serial_device_path_mock,
        serial_baud_rate=9600,
        shutdown_command=['touch', str(tmp_file)],
        shutdown_delay_s=1
    ))

    await hcu_skill.run()
    await asyncio.sleep(0.2)
    await write_serial_input(b'{"command":"SHUTDOWN"}\n')
    await asyncio.sleep(0.2)
    assert not tmp_file.exists()
    await asyncio.sleep(1)
    assert tmp_file.exists()

    await hcu_skill.close()

@pytest.mark.asyncio
async def test_resume(tmp_path, serial_device_path_mock, write_serial_input):
    tmp_file = tmp_path / 'shutdown_executed'

    hcu_skill = HcuSkill(HcuControllerConfig(
        enabled=True,
        serial_device=serial_device_path_mock,
        serial_baud_rate=9600,
        shutdown_command=['touch', str(tmp_file)],
        shutdown_delay_s=1
    ))

    await hcu_skill.run()
    await asyncio.sleep(0.2)
    await write_serial_input(b'{"command":"SHUTDOWN"}\n')
    await asyncio.sleep(0.2)
    await write_serial_input(b'{"command":"RESUME"}\n')
    await asyncio.sleep(1)
    assert not tmp_file.exists()

    await hcu_skill.close()
