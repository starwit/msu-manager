import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles

from .config import MsuManagerConfig
from .hcu import HcuController, HcuProtocol
from .hcu.messages import HcuMessage
from .uplink.monitor import UplinkMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


async def before_startup(app: FastAPI):
    CONFIG = MsuManagerConfig()
    app.state.CONFIG = CONFIG
    logger.info(f'Effective configuration: {CONFIG.model_dump_json(indent=2)}')

    logging.getLogger().setLevel(app.state.CONFIG.log_level.value)

    if CONFIG.hcu_controller.enabled:
        hcu_controller = HcuController(CONFIG.hcu_controller.shutdown_command, CONFIG.hcu_controller.shutdown_delay_s)
        app.state.hcu_controller = hcu_controller

        hcu_bind_address = CONFIG.hcu_controller.udp_bind_address
        hcu_listen_port = CONFIG.hcu_controller.udp_listen_port
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: HcuProtocol(controller=hcu_controller), local_addr=(hcu_bind_address, hcu_listen_port)
        )
        app.state.hcu_transport = transport
        app.state.hcu_protocol = protocol

        logger.info(f'Started HcuProtocol UDP listener on {hcu_bind_address}:{hcu_listen_port}')

    if CONFIG.uplink_monitor.enabled:
        uplink_monitor = UplinkMonitor(CONFIG.uplink_monitor)
        app.state.uplink_monitor = uplink_monitor
        app.state.uplink_monitor_task = asyncio.create_task(uplink_monitor.run())

        logger.info('Started UplinkMonitor')

async def after_shutdown(app: FastAPI):
    if app.state.CONFIG.hcu_controller.enabled:
        app.state.hcu_transport.close()

    if app.state.CONFIG.uplink_monitor.enabled:
        app.state.uplink_monitor_task.cancel()
        try:
            await app.state.uplink_monitor_task
        except asyncio.CancelledError:
            # Task cancellation is expected here as we've called cancel()
            pass
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    await before_startup(app)
    yield
    await after_shutdown(app)

app = FastAPI(lifespan=lifespan)

@app.get('/health', status_code=status.HTTP_204_NO_CONTENT)
async def health():
    pass

@app.post('/hcu-controller/command', status_code=status.HTTP_204_NO_CONTENT, responses={404: {}})
async def command_endpoint(command: HcuMessage):
    logger.info(f'Received {type(command).__name__} via HTTP: {command.model_dump_json(indent=2)}')
    if not app.state.CONFIG.hcu_controller.enabled:
        logger.warning('HcuController is disabled; ignoring command')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='HcuController is disabled')

    await app.state.hcu_controller.process_command(command)

app.mount("/", StaticFiles(directory="msu_manager/frontend",html = True), name="frontend")