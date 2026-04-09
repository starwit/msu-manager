import time

import pytest

from msu_manager.hcu.shutdown import ShutdownError, ShutdownModel


def test_start():
    testee = ShutdownModel(10)
    
    with pytest.raises(ShutdownError):
        _ = testee.time_remaining
    assert testee.is_active == False

    testee.start()
    
    assert abs(testee.time_remaining - 10) < 0.1
    assert testee.is_active == True

def test_multiple_starts():
    testee = ShutdownModel(10)

    testee.start()

    time.sleep(0.5)
    testee.start()  # Starting again should not reset the timer

    assert abs(testee.time_remaining - 9.5) < 0.1

def test_stop():
    testee = ShutdownModel(10)

    testee.start()
    testee.stop()

    with pytest.raises(ShutdownError):
        _ = testee.time_remaining
    
    assert testee.is_active == False

def test_reset():
    testee = ShutdownModel(10)

    testee.start()
    testee.reset()

    with pytest.raises(ShutdownError):
        _ = testee.time_remaining

    assert testee.is_active == False
    assert testee.is_inhibited == False

def test_nonnegative():
    testee = ShutdownModel(0)

    testee.start()
    time.sleep(0.3)
    
    assert testee.time_remaining == 0

def test_start_stop_start():
    testee = ShutdownModel(10)

    testee.start()
    testee.stop()
    testee.start()

    assert abs(testee.time_remaining - 10) < 0.1
    assert testee.is_active == True

def test_shutdown_start_inhibit():
    testee = ShutdownModel(10)

    testee.start()
    testee.inhibit(20)
    
    assert abs(testee.time_remaining - 20) < 0.1
    assert testee.is_active == True

def test_shutdown_inhibit_start():
    testee = ShutdownModel(10)

    testee.inhibit(20)
    testee.start()

    assert abs(testee.time_remaining - 20) < 0.1
    assert testee.is_active == True

def test_shutdown_start_inhibit_stop_start():
    testee = ShutdownModel(10)

    testee.start()
    testee.inhibit(20)
    testee.stop()
    testee.start()

    assert abs(testee.time_remaining - 20) < 0.1
    assert testee.is_active == True


def test_shutdown_start_inhibit_reset_start():
    testee = ShutdownModel(10)

    testee.start()

    testee.inhibit(20)

    testee.stop()

    testee.start()

    assert abs(testee.time_remaining - 20) < 0.1
    assert testee.is_active == True
