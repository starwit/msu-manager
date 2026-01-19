import asyncio
import logging
import os
from collections.abc import Iterable
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

async def run_command(command: Iterable[str] | str, env: Dict[str, str] = None, log_cmd: bool = False, log_err: bool = False, raise_on_fail: bool = False) -> Tuple[int, str, str]:
    if log_cmd:
        logger.info(f'Running command: {" ".join(command)} with env: {env}')
    
    if isinstance(command, str):
        command = [command]

    
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **env} if env else None
        )
        stdout, stderr = await proc.communicate()
        stdout = stdout.decode() if stdout else ''
        stderr = stderr.decode() if stderr else ''
        ret_code = proc.returncode
    except FileNotFoundError as e:
        # asyncio.create_subprocess_exec() raises FileNotFoundError if the program (i.e. the first entry of command) does not exist
        stdout = ''
        stderr = str(e)
        ret_code = -1


    logger.debug(f'Debug output of "{" ".join(command)}", env: {env}')
    logger.debug(f"STDOUT:")
    logger.debug(f"{stdout}")
    logger.debug(f"STDERR:")
    logger.debug(f"{stderr}")

    if log_err and ret_code != 0:
        logger.error(f'Error running "{" ".join(command)}"')
        logger.error(f"STDOUT:")
        logger.error(f"{stdout}")
        logger.error(f"STDERR:")
        logger.error(f"{stderr}")

    if raise_on_fail and ret_code != 0:
        raise IOError(f'Failed running "{" ".join(command)}"\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}')

    return ret_code, stdout, stderr

async def run_sudo_command(command: Iterable[str] | str, env: Dict[str, str] = None, log_cmd: bool = False, log_err: bool = False, raise_on_fail: bool = False) -> Tuple[int, str, str]:
    sudo_command = ['sudo', '-n'] + ([command] if isinstance(command, str) else list(command))
    return await run_command(sudo_command, env=env, log_cmd=log_cmd, log_err=log_err, raise_on_fail=raise_on_fail)