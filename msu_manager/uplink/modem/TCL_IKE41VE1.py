import asyncio
import json
import logging
from collections.abc import Iterable
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

from ...command import run_command
from ..status import Ping

logger = logging.getLogger(__name__)

# Add dummy modem to config with configurable command or return value
# Add configuration values for this one
# How can we possibly test this?

class ModemState(str, Enum):
    REGISTERED = "registered"
    ENABLED = "enabled"
    CONNECTED = "connected"


class TCL_IKE41VE1:
    def __init__(self, ping: Ping, apn: str = "internet.telekom", wwan_iface: str = "wwan0"):
        self._ping = ping
        self._reboot_threshold_s = 300
        self._apn = apn
        self._wwan_iface = wwan_iface

    async def reconnect(self) -> None:
        try:
            # Wait for modem hardware
            if not await self._wait_for_hardware():
                logger.info('Failed to detect modem, trying to restart ModemManager')
                await self._restart_modemmanager()
                if not await self._wait_for_hardware():
                    raise RuntimeError('Modem detection failed after ModemManager restart')
            
            # Try simple connect first
            logger.info('Trying simple-connect')
            if await self._connect_bearer() and await self._set_up_network_interface() and await self._check_connection():
                logger.info('Connection successful')
                return
            
            # Simple connect failed, reset modem
            logger.info('Simple-connect failed, resetting modem')
            await self._reset_modem()
            
            if not await self._wait_for_modem_reset():
                logger.error('Reset failed')
                await self._log_modem_status()
                raise RuntimeError('Modem reset failed')
            
            if not await self._wait_for_hardware():
                logger.error('Modem failed to register with the OS after reset')
                await self._log_modem_status()
                raise RuntimeError('Modem failed to register after reset')
            
            if not await self._wait_for_modem_ready():
                logger.error('Modem failed to get ready')
                await self._log_modem_status()
                raise RuntimeError('Modem failed to get ready')
            
            # Try to connect again after reset
            if await self._connect_bearer() and await self._set_up_network_interface() and await self._check_connection():
                logger.info('Connection successful after reset')
                return
            else:
                logger.error('Connection finally failed')
                await self._log_modem_status()
                raise RuntimeError('Connection failed after reset')
                
        except Exception:
            logger.warning(f'Failed to reconnect', exc_info=True)
            raise

    async def _restart_modemmanager(self) -> None:
        logger.info('Restarting ModemManager.service')
        await run_command(('sudo', '-n', 'systemctl', 'restart', 'ModemManager.service'), log_cmd=True, log_err=True)
    
    async def _connect_bearer(self) -> bool:
        modem_id = await self._get_modem_id()
        if not modem_id:
            logger.error('Failed to get modem ID')
            return False
        
        logger.info(f'Connecting to APN {self._apn} on modem {modem_id}...')

        ret_code, _, _ = await run_command((
            'mmcli', '-m', str(modem_id),
            f'--simple-connect=apn={self._apn},ip-type=ipv4,allow-roaming=true'
        ), log_cmd=True)
        if ret_code != 0:
            logger.error('Failed to connect modem')
            return False
        
        if await self._wait_for_modem_connected():
            logger.info('Modem connected')
            return True
        else:
            logger.error('Modem not connected')
            return False
        
    async def _set_up_network_interface(self) -> bool:
        logger.info('Setting up network interface')
        
        modem_id = await self._get_modem_id()
        if not modem_id:
            logger.error('Failed to get modem ID')
            return False
        
        logger.info(f'Using modem with ID {modem_id}')
        await self._log_modem_status()
        
        # Get bearer info
        bearers = await self._get_modem_json_value('modem', 'generic', 'bearers')
        if not bearers:
            logger.error('Failed to get bearers list')
            return False
        
        try:
            bearer_path = bearers[0]
            bearer_id = bearer_path.split('/')[-1]
        except (IndexError, AttributeError) as e:
            logger.error(f'Failed to extract bearer ID: {e}')
            return False
        
        logger.info(f'Using bearer with ID {bearer_id}')
        
        # Get bearer IP configuration
        bearer_ip = await self._get_bearer_json_value(bearer_id, ('bearer', 'ipv4-config', 'address'))
        bearer_gw = await self._get_bearer_json_value(bearer_id, ('bearer', 'ipv4-config', 'gateway'))
        bearer_ip_prefix = await self._get_bearer_json_value(bearer_id, ('bearer', 'ipv4-config', 'prefix'))
        bearer_dns_list = await self._get_bearer_json_value(bearer_id, ('bearer', 'ipv4-config', 'dns'))
        
        logger.info('Using IP info from bearer:')
        logger.info(f'BEARER_IP: {bearer_ip}')
        logger.info(f'BEARER_GW: {bearer_gw}')
        logger.info(f'BEARER_IP_PREFIX: {bearer_ip_prefix}')
        logger.info(f'BEARER_DNS: {bearer_dns_list}')
        
        if not all([bearer_ip, bearer_gw, bearer_ip_prefix, bearer_dns_list]):
            logger.error('No valid IP info — aborting. ❌')
            return False
        
        logger.info(f'Setting up {self._wwan_iface}...')
        
        # Configure interface
        await run_command(('ip', 'addr', 'flush', 'dev', self._wwan_iface), log_cmd=True, raise_on_fail=True)
        await run_command(('ip', 'link', 'set', self._wwan_iface, 'up'), log_cmd=True, raise_on_fail=True)
        await run_command(('ip', 'addr', 'add', f'{bearer_ip}/{bearer_ip_prefix}', 'dev', self._wwan_iface), log_cmd=True, raise_on_fail=True)
        
        logger.info('Setting DNS servers')
        await run_command(('resolvectl', 'dns', self._wwan_iface, *bearer_dns_list), log_cmd=True, raise_on_fail=True)
        
        logger.info('Setting default IP route')
        await run_command(('ip', 'route', 'add', 'default', 'via', bearer_gw, 'metric', '500'), log_cmd=True, raise_on_fail=True)
        
        logger.info('Network interface configuration done')
        return True
    
    async def _check_connection(self) -> bool:
        return await self._ping.check()
    
    async def _reset_modem(self) -> None:
        at_port = await self._get_modem_at_port()
        if not at_port:
            raise RuntimeError('Failed to get AT port for modem reset')
        
        logger.info(f'Resetting modem via AT command on {at_port}')
        try:
            with open(at_port, 'w') as f:
                f.write('AT&F\r\n')
        except Exception as e:
            raise RuntimeError(f'Failed to send reset command to modem: {e}')

    async def _wait_for_hardware(self, timeout_s=90) -> bool:
        logger.info(f'Waiting for ModemManager to pick up modem (timeout {timeout_s}s)')
        await run_command(('mmcli', '-S'))
        
        async def detected():
            ret_code, _, _ = await run_command(('mmcli', '-m', 'any'))
            return ret_code == 0

        return await self._wait_for_modem_condition(detected, timeout_s)
    
    async def _wait_for_modem_reset(self, timeout_s=20) -> bool:
        logger.info(f'Waiting for modem to reset (timeout {timeout_s}s)')

        async def reset():
            ret_code, _, _ = await run_command(('mmcli', '-m', 'any'))
            return ret_code != 0
        
        return await self._wait_for_modem_condition(reset, timeout_s)
        
    async def _wait_for_modem_ready(self, timeout_s=20) -> bool:
        logger.info(f'Waiting for modem to be ready (timeout {timeout_s}s)')

        async def ready():
            state = await self._get_modem_state()
            return state in [ModemState.REGISTERED, ModemState.ENABLED, ModemState.CONNECTED]
        
        return await self._wait_for_modem_condition(ready, timeout_s)
        
    async def _wait_for_modem_connected(self, timeout_s=60) -> bool:
        logger.info(f'Waiting for modem to be connected (timeout {timeout_s}s)')

        async def connected():
            state = await self._get_modem_state()
            return state == ModemState.CONNECTED
        
        return await self._wait_for_modem_condition(connected, timeout_s)
    
    async def _wait_for_modem_condition(self, condition: Callable[[], Awaitable[bool]], timeout_s) -> bool:
        for i in range(timeout_s):
            if await condition():
                logger.info(f'Modem condition "{condition.__name__}" met after {i} seconds.')
                return True
            await asyncio.sleep(1)
        
        logger.info(f'Modem condition "{condition.__name__}" not met after {timeout_s} seconds.')
        return False

    def _parse_json(self, json_str: str) -> Optional[dict]:
        """Parse JSON string and handle exceptions."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse JSON: {e}')
            return None
        
    async def _get_command_json_value(self, command: Iterable[str], path: Iterable[str]) -> Optional[Any]:
        """Get a value from command JSON output using a key path.
        
        Example: _get_command_json_value(('mmcli', '-m', 'any', '-J'), ('modem', 'generic', 'state'))
        """
        ret_code, stdout, _ = await run_command(command, log_err=True)
        if ret_code != 0:
            return None
        
        data = self._parse_json(stdout)
        if not data:
            return None
        
        try:
            result = data
            for key in path:
                result = result[key]
            return result
        except (KeyError, TypeError) as e:
            logger.error(f'Failed to extract value at path {".".join(path)}: {e}')
            return None

    async def _get_modem_json_value(self, path: Iterable[str]) -> Optional[Any]:
        return await self._get_command_json_value(('mmcli', '-m', 'any', '-J'), path)

    async def _get_bearer_json_value(self, bearer_id: str, path: Iterable[str]) -> Optional[Any]:
        return await self._get_command_json_value(('mmcli', '-b', bearer_id, '-J'), path)

    async def _get_modem_state(self) -> Optional[str]:
        return await self._get_modem_json_value(('modem', 'generic', 'state'))

    async def _get_modem_id(self) -> Optional[str]:
        dbus_path = await self._get_modem_json_value(('modem', 'dbus-path'))
        if not dbus_path:
            return None
        return dbus_path.split('/')[-1]

    async def _get_modem_at_port(self) -> Optional[str]:
        ports = await self._get_modem_json_value(('modem', 'generic', 'ports'))
        if not ports:
            return None
        
        try:
            at_ports = sorted([p for p in ports if 'at' in p.lower()])
            if not at_ports:
                logger.error(f'Modem has no AT ports (ports: {ports})')
                return None
            # Use the last AT port (secondary)
            device_name = at_ports[-1].split()[0]
            return f'/dev/{device_name}'
        except (AttributeError, IndexError) as e:
            logger.error(f'Failed to extract AT port: {e}')
            return None

    async def _log_modem_status(self) -> None:
        ret_code, stdout, _ = await run_command(('mmcli', '-m', 'any'), log_err=True)
        if ret_code == 0:
            logger.info(f'Modem status:\n{stdout}')
    