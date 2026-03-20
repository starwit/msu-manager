import asyncio

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def test_client(default_testee, write_serial_input):
    app = FastAPI()
    default_testee.add_routes(app.router)
    await default_testee.run()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        yield client
        
    await default_testee.close()
    

@pytest.mark.asyncio
async def test_shutdown_inhibit_ongoing(tmp_shutdown_file, test_client, write_serial_input):
    await write_serial_input(b'{"type":"SHUTDOWN"}\n')
    await asyncio.sleep(0.01)
    await test_client.get('/shutdown/inhibit/2')
    assert not tmp_shutdown_file.exists()
    await asyncio.sleep(1.5)
    assert not tmp_shutdown_file.exists()
    await asyncio.sleep(1)
    assert tmp_shutdown_file.exists()

