import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import MsuManagerConfig
from .hcu import close as close_hcu
from .hcu import init as init_hcu
from .uplink import close as close_uplink_monitor
from .uplink import init as init_uplink_monitor

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
        init_hcu(app, CONFIG.hcu_controller)

    if CONFIG.uplink_monitor.enabled:
        init_uplink_monitor(app, CONFIG.uplink_monitor)

async def after_shutdown(app: FastAPI):
    if app.state.CONFIG.hcu_controller.enabled:
        close_hcu(app)

    if app.state.CONFIG.uplink_monitor.enabled:
        close_uplink_monitor(app)
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    await before_startup(app)
    yield
    await after_shutdown(app)

app = FastAPI(lifespan=lifespan)
