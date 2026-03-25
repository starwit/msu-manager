import asyncio

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_shutdown_inhibit_ongoing(default_hcu_skill, tmp_shutdown_file, write_serial_input):
    app = FastAPI()
    default_hcu_skill.add_routes(app.router)
    await default_hcu_skill.run()
    await asyncio.sleep(0.01)  # Give the skill some time to start and set up the serial connection
        
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as test_client:    
        await write_serial_input(b'{"type":"SHUTDOWN"}\n')
        await asyncio.sleep(0.01)
        await test_client.get('/shutdown/inhibit/2')
        assert not tmp_shutdown_file.exists()
        await asyncio.sleep(1.5)
        assert not tmp_shutdown_file.exists()
        await asyncio.sleep(1)
        assert tmp_shutdown_file.exists()

    await default_hcu_skill.close()

@pytest.mark.asyncio
async def test_shutdown_inhibit_remaining_api(default_hcu_skill, write_serial_input):
    app = FastAPI()
    default_hcu_skill.add_routes(app.router)
    await default_hcu_skill.run()
    await asyncio.sleep(0.01)  # Give the skill some time to start and set up the serial connection
        
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as test_client:    
        await write_serial_input(b'{"type":"SHUTDOWN"}\n')
        await asyncio.sleep(0.01)

        response = await test_client.get('/shutdown/remaining')
        print(response.content)
        assert response.status_code == 200
        assert abs(float(response.content) - 1) < 0.1

        await test_client.get('/shutdown/inhibit/2')

        response = await test_client.get('/shutdown/remaining')
        print(response.content)
        assert response.status_code == 200
        assert abs(float(response.content) - 2) < 0.1

    await default_hcu_skill.close()

