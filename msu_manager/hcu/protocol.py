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
            logger.debug(f'Received raw message from HCU')
            raw_message, self._buffer = self._buffer.split('\n', maxsplit=1)
            self._process_message(raw_message)

    def _process_message(self, message: str) -> None:
        try:
            json_dict = json.loads(message.strip())
        except (UnicodeDecodeError, JSONDecodeError):
            logger.error(f'Failed to parse JSON message from HCU: {message.strip()}')
            logger.debug(f'Decode error', exc_info=True)
            return
        
        message_obj = validate_python_message(json_dict)
        logger.debug(f'Received {type(message_obj).__name__} from HCU: {message_obj.model_dump_json(indent=2)}')

        if self._controller:
            asyncio.create_task(self._controller.process_message(message_obj))

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connection_lost(self, exc):
        logger.debug('HcuProtocol serial listener stopped', exc_info=exc)
        self._is_connected = False
    
    def close(self) -> None:
        self._transport.close()
