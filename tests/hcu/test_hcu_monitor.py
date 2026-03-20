import asyncio

import pytest

from msu_manager.config import HcuControllerConfig
from msu_manager.hcu.skill import HcuSkill


@pytest.mark.asyncio
async def test_shutdown(tmp_shutdown_file, serial_device_path_mock, write_serial_input):

    hcu_skill = HcuSkill(HcuControllerConfig(
        enabled=True,
        serial_device=serial_device_path_mock,
        serial_baud_rate=9600,
        shutdown_command=['touch', str(tmp_shutdown_file)],
        shutdown_delay_s=1
    ))

    await hcu_skill.run()
    await asyncio.sleep(0.2)
    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.2)
    assert not tmp_shutdown_file.exists()
    await asyncio.sleep(1)
    assert tmp_shutdown_file.exists()

    await hcu_skill.close()

@pytest.mark.asyncio
async def test_resume(tmp_shutdown_file, serial_device_path_mock, write_serial_input):

    hcu_skill = HcuSkill(HcuControllerConfig(
        enabled=True,
        serial_device=serial_device_path_mock,
        serial_baud_rate=9600,
        shutdown_command=['touch', str(tmp_shutdown_file)],
        shutdown_delay_s=1
    ))

    await hcu_skill.run()
    await asyncio.sleep(0.2)
    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.2)
    await write_serial_input(b'{"type":"RESUME"}\n')
    await asyncio.sleep(1)
    assert not tmp_shutdown_file.exists()

    await hcu_skill.close()

@pytest.mark.asyncio
async def test_shutdown_failing(serial_device_path_mock, write_serial_input):
    hcu_skill = HcuSkill(HcuControllerConfig(
        enabled=True,
        serial_device=serial_device_path_mock,
        serial_baud_rate=9600,
        shutdown_command=['false'],
        shutdown_delay_s=0
    ))

    await hcu_skill.run()
    await asyncio.sleep(0.2)
    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.2)

    await hcu_skill.close()