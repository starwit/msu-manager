
import logging
import asyncio
import os
from typing import Dict, List, Tuple

from ..config import UplinkMonitorConfig

logger = logging.getLogger(__name__)

class UplinkMonitor:
    def __init__(self, config: UplinkMonitorConfig):
        self._restore_connection_cmd = config.restore_connection_cmd
        self._restore_connection_env = {
            'WWAN_IFACE': config.wwan_device,
            'APN': config.wwan_apn,
        }
        self._check_connection_cmd = [
            'ping',
            '-c', '3',
            '-w', '1',
            '-i', '0.2',
            *(['-I', config.check_connection_device] if config.check_connection_device else []),
            config.check_connection_target,
        ]
        self._check_interval_s = config.check_interval_s

    async def run(self):
        try:
            while True:
                is_up = await self.check_connection()
                logger.debug(f'Connection status: {"up" if is_up else "down"}')
                if not is_up:
                    logger.warning("Connection is down, attempting to restore...")
                    success = await self.restore_connection()
                    if success:
                        logger.info("Connection restored successfully.")
                    else:
                        logger.error("Failed to restore connection.")
                await asyncio.sleep(self._check_interval_s)
        except asyncio.CancelledError:
            logger.info("UplinkMonitor task cancelled.")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred in UplinkMonitor", exc_info=True)

    async def check_connection(self) -> bool:
        ret_code, stdout, stderr = await self._run_command(self._check_connection_cmd)

        if ret_code == 0:
            return True
        else:
            logger.error(f'Connection check failed. Output of {" ".join(self._check_connection_cmd)}')
            logger.error(f"STDOUT:")
            logger.error(f"{stdout}")
            logger.error(f"STDERR:")
            logger.error(f"{stderr}")
            return False

    async def restore_connection(self) -> bool:
        ret_code, stdout, stderr = await self._run_command(self._restore_connection_cmd, env=self._restore_connection_env)

        if ret_code == 0:
            return True
        else:
            logger.error(f"Failed to restore connection. Output of {' '.join(self._restore_connection_cmd)}")
            logger.error(f"STDOUT:")
            logger.error(f"{stdout}")
            logger.error(f"STDERR:")
            logger.error(f"{stderr}")
            return False

    async def _run_command(self, command: List[str], env: Dict[str, str] = None) -> Tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **env} if env else None
        )
        stdout, stderr = await proc.communicate()
        stdout = stdout.decode() if stdout else ''
        stderr = stderr.decode() if stderr else ''
        return proc.returncode, stdout, stderr
