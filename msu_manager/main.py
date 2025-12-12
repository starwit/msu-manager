import logging
from contextlib import asynccontextmanager

import prometheus_client
from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from .config import MsuManagerConfig
from .hcu import HcuSkill
from .uplink import UplinkSkill


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
        hcu = HcuSkill(CONFIG.hcu_controller)
        hcu_router = APIRouter(prefix='/api/hcu')
        hcu.add_routes(hcu_router)
        await hcu.run()
        app.state.hcu_skill = hcu
        app.include_router(hcu_router)

    if CONFIG.uplink_monitor.enabled:
        uplink = UplinkSkill(CONFIG.uplink_monitor)
        uplink_router = APIRouter(prefix='/api/uplink')
        uplink.add_routes(uplink_router)
        await uplink.run()
        app.state.uplink_skill = uplink
        app.include_router(uplink_router)
        
    if CONFIG.frontend.enabled:
        app.mount("/", StaticFiles(directory=CONFIG.frontend.path,html = True), name="frontend")

async def after_shutdown(app: FastAPI):
    if app.state.CONFIG.hcu_controller.enabled:
        await app.state.hcu_skill.close()

    if app.state.CONFIG.uplink_monitor.enabled:
        await app.state.uplink_skill.close()
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    await before_startup(app)
    yield
    await after_shutdown(app)

app = FastAPI(lifespan=lifespan)
app.mount('/api/metrics', prometheus_client.make_asgi_app())
