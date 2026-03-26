import asyncio
from typing import List

import pytest
import pytest_asyncio

from msu_manager.config import HcuControllerConfig
from msu_manager.hcu.skill import HcuSkill


@pytest_asyncio.fixture
async def make_hcu_skill(serial_device_path_mock, write_serial_input):
    skill = None
    
    async def factory(shutdown_command: List[str], shutdown_delay_s: int) -> HcuSkill:
        nonlocal skill
        skill = HcuSkill(HcuControllerConfig(
            enabled=True,
            serial_device=serial_device_path_mock,
            serial_baud_rate=9600,
            shutdown_command=shutdown_command,
            shutdown_delay_s=shutdown_delay_s
        ))
        await skill.run()
        await asyncio.sleep(0.01)
        return skill
    
    yield factory

    await skill.close()


@pytest.mark.asyncio
async def test_shutdown(tmp_shutdown_file, make_hcu_skill, write_serial_input):

    _ = await make_hcu_skill(
        shutdown_command=['touch', str(tmp_shutdown_file)],
        shutdown_delay_s=1
    )

    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.2)
    assert not tmp_shutdown_file.exists()
    await asyncio.sleep(1)
    assert tmp_shutdown_file.exists()

@pytest.mark.asyncio
async def test_resume(tmp_shutdown_file, make_hcu_skill, write_serial_input):

    _ = await make_hcu_skill(
        shutdown_command=['touch', str(tmp_shutdown_file)],
        shutdown_delay_s=1
    )

    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.2)
    await write_serial_input(b'{"type":"RESUME"}\n')
    await asyncio.sleep(1)
    assert not tmp_shutdown_file.exists()

@pytest.mark.asyncio
async def test_repeated_shutdown_resume(tmp_shutdown_file, make_hcu_skill, write_serial_input):

    _ = await make_hcu_skill(
        shutdown_command=['touch', str(tmp_shutdown_file)],
        shutdown_delay_s=1
    )

    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.5)
    await write_serial_input(b'{"type":"RESUME"}\n')
    await asyncio.sleep(0.1)
    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.6)
    assert not tmp_shutdown_file.exists()
    await asyncio.sleep(0.5)
    assert tmp_shutdown_file.exists()

@pytest.mark.asyncio
async def test_shutdown_failing(make_hcu_skill, write_serial_input):
    _ = await make_hcu_skill(
        shutdown_command=['false'],
        shutdown_delay_s=0
    )

    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.2)