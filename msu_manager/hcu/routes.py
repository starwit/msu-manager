import logging

from fastapi import APIRouter, FastAPI, HTTPException, status

from .messages import HcuMessage

logger = logging.getLogger(__name__)

def setup_routes(app: FastAPI):
    router = APIRouter()

    @router.post('/command', status_code=status.HTTP_204_NO_CONTENT, responses={404: {}})
    async def command_endpoint(command: HcuMessage):
        logger.info(f'Received {type(command).__name__} via HTTP: {command.model_dump_json(indent=2)}')
        if not app.state.CONFIG.hcu_controller.enabled:
            logger.warning('HcuController is disabled; ignoring command')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='HcuController is disabled')

        await app.state.hcu_controller.process_command(command)

    app.include_router(router, prefix='/api/hcu')