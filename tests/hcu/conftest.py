import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from msu_manager.config import HcuControllerConfig
from msu_manager.hcu.skill import HcuSkill


@pytest.fixture
def tmp_shutdown_file(tmp_path) -> Path:
    return tmp_path / 'shutdown_executed'

@pytest.fixture
def default_testee(tmp_shutdown_file, serial_device_path_mock):
    return HcuSkill(HcuControllerConfig(
        enabled=True,
        serial_device=serial_device_path_mock,
        serial_baud_rate=9600,
        shutdown_command=['touch', str(tmp_shutdown_file)],
        shutdown_delay_s=1
    ))

@pytest_asyncio.fixture
async def write_serial_input(unused_tcp_port):
    dummy_writer = None

    def connect_cb(_, writer):
        nonlocal dummy_writer
        dummy_writer = writer
    
    await asyncio.start_server(connect_cb, '127.0.0.1', unused_tcp_port)

    async def writer(data: bytes):
        assert dummy_writer is not None, 'You need to make sure the serial connection is established before calling write_serial_input()'
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