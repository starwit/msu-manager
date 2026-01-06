import asyncio
import json
import logging
from json import JSONDecodeError

from .controller import HcuController
from .messages import validate_python_message

logger = logging.getLogger(__name__)


class HcuProtocol(asyncio.Protocol):
    def __init__(self, controller: HcuController = None):
        self._controller = controller
        self._transport = None
        self._buffer = ''
        self._is_connected = False
        
    def connection_made(self, transport: asyncio.Transport) -> None:
        self._transport = transport
        self._is_connected = True

    def data_received(self, data: bytes) -> None:
        logger.debug(f'Received {len(data)} bytes from HCU: {data.hex()}')

        self._buffer += data.decode(encoding='ascii', errors='ignore')

        while '\n' in self._buffer:
            logger.debug(f'Received raw command from HCU')
            raw_command, self._buffer = self._buffer.split('\n', maxsplit=1)
            self._process_command(raw_command)

    def _process_command(self, command: str) -> None:
        try:
            json_dict = json.loads(command.strip())
        except (UnicodeDecodeError, JSONDecodeError):
            logger.error(f'Failed to parse JSON command from HCU: {command.strip()}')
            logger.debug(f'Decode error', exc_info=True)
            return
        
        command = validate_python_message(json_dict)
        logger.debug(f'Received {type(command).__name__} from HCU: {command.model_dump_json(indent=2)}')

        if self._controller:
            asyncio.create_task(self._controller.process_command(command))

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connection_lost(self, exc):
        logger.debug('HcuProtocol serial listener stopped', exc_info=exc)
        self._is_connected = False
    
    def close(self) -> None:
        self._transport.close()
