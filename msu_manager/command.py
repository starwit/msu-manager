import asyncio
import logging
import os
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

async def run_command(command: List[str], env: Dict[str, str] = None) -> Tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, **env} if env else None
    )
    stdout, stderr = await proc.communicate()
    stdout = stdout.decode() if stdout else ''
    stderr = stderr.decode() if stderr else ''

    logger.debug(f'Debug output of {" ".join(command)}, env: {env}')
    logger.debug(f"STDOUT:")
    logger.debug(f"{stdout}")
    logger.debug(f"STDERR:")
    logger.debug(f"{stderr}")

    return proc.returncode, stdout, stderr