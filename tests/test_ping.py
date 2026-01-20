from textwrap import dedent

import pytest

from msu_manager.config import PingConfig
from msu_manager.uplink.status import Ping


@pytest.fixture
def dummy_ping_instance():
    config = PingConfig(
        target='127.0.0.1',
        interface=None,
    )
    return Ping(config)

def test_parse_successful_ping_output(dummy_ping_instance):
    output = dedent('''
        PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.
        64 bytes from 1.1.1.1: icmp_seq=1 ttl=56 time=11.0 ms
        64 bytes from 1.1.1.1: icmp_seq=2 ttl=56 time=13.9 ms

        --- 1.1.1.1 ping statistics ---
        2 packets transmitted, 2 received, 0% packet loss, time 1001ms
        rtt min/avg/max/mdev = 10.960/12.434/13.909/1.474 ms
    ''').strip()

    result = dummy_ping_instance._parse_ping_output(output)

    assert result.packets_transmitted == 2
    assert result.packets_received == 2
    assert result.rtt_min == 10.960
    assert result.rtt_avg == 12.434
    assert result.rtt_max == 13.909
    assert result.rtt_mdev == 1.474

def test_parse_ping_output_with_packet_loss(dummy_ping_instance):
    output = dedent('''
        PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.
        64 bytes from 1.1.1.1: icmp_seq=1 ttl=56 time=11.0 ms

        --- 1.1.1.1 ping statistics ---
        5 packets transmitted, 1 received, 80% packet loss, time 4003ms
        rtt min/avg/max/mdev = 11.000/11.000/11.000/0.000 ms
    ''').strip()

    result = dummy_ping_instance._parse_ping_output(output)

    assert result.packets_transmitted == 5
    assert result.packets_received == 1
    assert result.rtt_min == 11.000
    assert result.rtt_avg == 11.000
    assert result.rtt_max == 11.000
    assert result.rtt_mdev == 0.000

def test_parse_ping_output_total_loss(dummy_ping_instance):
    output = dedent('''
        PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.

        --- 1.1.1.1 ping statistics ---
        3 packets transmitted, 0 received, 100% packet loss, time 2047ms
    ''').strip()

    result = dummy_ping_instance._parse_ping_output(output)

    assert result.packets_transmitted == 3
    assert result.packets_received == 0
    assert result.rtt_min == 0.0
    assert result.rtt_avg == 0.0
    assert result.rtt_max == 0.0
    assert result.rtt_mdev == 0.0

def test_parse_ping_output_invalid_format(dummy_ping_instance):
    output = 'Some invalid output without statistics'

    result = dummy_ping_instance._parse_ping_output(output)

    assert result is None

def test_parse_ping_output_with_different_spacing(dummy_ping_instance):
    output = dedent('''
        PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
        64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=5.23 ms

        --- 8.8.8.8 ping statistics ---
        10 packets transmitted,  10 received, 0% packet loss, time 9013ms
        rtt min/avg/max/mdev = 5.230/6.145/8.910/1.023 ms
    ''').strip()

    result = dummy_ping_instance._parse_ping_output(output)

    assert result.packets_transmitted == 10
    assert result.packets_received == 10
    assert result.rtt_min == 5.230
    assert result.rtt_avg == 6.145
    assert result.rtt_max == 8.910
    assert result.rtt_mdev == 1.023

@pytest.mark.asyncio
async def test_run_localhost(tmp_path):
    # This test will actually run the ping command to localhost.
    config = PingConfig(
        target='127.0.0.1',
    )
    ping_instance = Ping(config, interface='lo')

    result = await ping_instance.check()

    assert result == True

@pytest.mark.asyncio
async def test_run_non_existing_target(tmp_path):
    # This test will actually run the ping command to a non-existing IP address
    config = PingConfig(
        target='198.51.100.123', # This is reserved, see https://en.wikipedia.org/wiki/Reserved_IP_addresses
    )
    ping_instance = Ping(config, interface='lo')

    result = await ping_instance.check()

    assert result == False

@pytest.mark.asyncio
async def test_run_non_existing_interface(tmp_path):
    # This test will actually run the ping command through a non-existing interface
    config = PingConfig(target='127.0.0.1')
    ping_instance = Ping(config, interface='DOES_NOT_EXIST')

    result = await ping_instance.check()

    assert result == False