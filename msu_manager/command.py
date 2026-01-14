import asyncio
import logging
import os
from collections.abc import Iterable
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

async def run_command(command: Iterable[str], env: Dict[str, str] = None, log_cmd: bool = False, log_err: bool = False, raise_on_fail: bool = False) -> Tuple[int, str, str]:
    if log_cmd:
        logger.info(f'Running command: {" ".join(command)} with env: {env}')
    
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

    if log_err and proc.returncode != 0:
        logger.error(f'Error running ({" ".join(command)})')
        logger.error(f"STDOUT:")
        logger.error(f"{stdout}")
        logger.error(f"STDERR:")
        logger.error(f"{stderr}")

    if raise_on_fail and proc.returncode != 0:
        raise IOError(f'Failed running ({" ".join(command)})', f'STDOUT: {stdout.replace("\n", "; ")}', f'STDERR: {stderr.replace("\n", "; ")}')

    return proc.returncode, stdout, stderr