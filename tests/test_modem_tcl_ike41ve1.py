import logging

import pytest

from msu_manager.config import PingConfig
from msu_manager.uplink.modem.TCL_IKE41VE1 import TCL_IKE41VE1
from msu_manager.uplink.status import Ping


@pytest.mark.asyncio
async def test_tcl_ike41ve1_modem_reconnect(request, caplog):
    caplog.set_level(logging.DEBUG)
    
    if 'tests/test_modem_tcl_ike41ve1.py' not in request.config.args:
        pytest.skip("Skipping TCL IKE41VE1 modem tests (specify tests/test_modem_tcl_ike41ve1.py explicitly to enable)")
    
    ping_instance = Ping(PingConfig(
        target='1.1.1.1',
        interface='wwan0',
    ))
    modem = TCL_IKE41VE1(ping_instance)
    await modem.reconnect()

    assert await ping_instance.check() == True