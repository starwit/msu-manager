import asyncio

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

@pytest_asyncio.fixture
async def test_client(default_hcu_skill, write_serial_input):
    # write_serial input must be requested as a fixture to ensure the serial connection is established before hcu skill tries to connect to it
    _ = write_serial_input

    app = FastAPI()
    default_hcu_skill.add_routes(app.router)
    await default_hcu_skill.run()
    await asyncio.sleep(0.01)  # Give the skill one iteration of its loop to ensure it's fully started before tests run

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:   
        yield client
    await default_hcu_skill.close()

@pytest.mark.asyncio
async def test_shutdown_inhibit_ongoing(test_client, tmp_shutdown_file, write_serial_input):
    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.01)
    await test_client.put('/shutdown/inhibit/2')
    assert not tmp_shutdown_file.exists()
    await asyncio.sleep(1.5)
    assert not tmp_shutdown_file.exists()
    await asyncio.sleep(1)
    assert tmp_shutdown_file.exists()

@pytest.mark.asyncio
async def test_shutdown_inhibit_api(test_client, tmp_shutdown_file, write_serial_input):
    response = await test_client.get('/shutdown/inhibit/2')
    assert response.status_code == 405      # Method not allowed
    
    response = await test_client.put('/shutdown/inhibit/-2')
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_shutdown_inhibit_status_api(test_client, write_serial_input):
    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.01)

    response = await test_client.get('/shutdown/status')
    assert response.status_code == 200
    assert abs(float(response.json()['remaining_runtime_s']) - 1) < 0.1
    assert bool(response.json()['shutdown_in_progress']) == True

    await test_client.put('/shutdown/inhibit/2')

    response = await test_client.get('/shutdown/status')
    assert response.status_code == 200
    assert abs(float(response.json()['remaining_runtime_s']) - 2) < 0.1
    assert bool(response.json()['shutdown_in_progress']) == True
