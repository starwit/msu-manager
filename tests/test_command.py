from msu_manager.command import run_command, run_sudo_command

import pytest

@pytest.mark.asyncio
async def test_run_command_echo_stdout():
    ret_code, stdout, stderr = await run_command(('echo', 'Hello, World!'), log_cmd=True, log_err=True)
    assert ret_code == 0
    assert stdout.strip() == 'Hello, World!'
    assert stderr.strip() == ''

@pytest.mark.asyncio
async def test_run_command_nonexistent_noargs():
    ret_code, stdout, stderr = await run_command('nonexistent_command', log_cmd=True, log_err=True)
    assert ret_code != 0
    assert stdout.strip() == ''
    assert 'No such file' in stderr

@pytest.mark.asyncio
async def test_run_sudo_command_failing():
    ret_code, stdout, stderr = await run_sudo_command(('definitely', 'fails_without_pw'), log_cmd=True, log_err=True)
    assert ret_code != 0
    assert stdout == ''
    assert 'a password is required' in stderr

@pytest.mark.asyncio
async def test_run_sudo_command_failing_noargs():
    ret_code, stdout, stderr = await run_sudo_command('fails_without_pw', log_cmd=True, log_err=True)
    assert ret_code != 0
    assert stdout == ''
    assert 'a password is required' in stderr

@pytest.mark.asyncio
async def test_run_command_raise_on_fail():
    with pytest.raises(IOError):
        await run_command(('false',), raise_on_fail=True)