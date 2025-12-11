import asyncio
import logging

from fastapi import FastAPI

from ..config import HcuControllerConfig
from .controller import HcuController
from .messages import HcuMessage
from .protocol import HcuProtocol

logger = logging.getLogger(__name__)


async def init(app: FastAPI, config: HcuControllerConfig):
    hcu_controller = HcuController(config.shutdown_command, config.shutdown_delay_s)
    app.state.hcu_controller = hcu_controller

    hcu_bind_address = config.udp_bind_address
    hcu_listen_port = config.udp_listen_port
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: HcuProtocol(controller=hcu_controller), local_addr=(hcu_bind_address, hcu_listen_port)
    )
    app.state.hcu_transport = transport
    app.state.hcu_protocol = protocol

    logger.info(f'Started HcuProtocol UDP listener on {hcu_bind_address}:{hcu_listen_port}')


async def close(app: FastAPI):
    app.state.hcu_transport.close()

    logger.info('Stopped HcuProtocol UDP listener')