import pytest
from pydantic_core import ValidationError

from msu_manager.hcu.messages import (HeartbeatMessage, LogMessage,
                                      ResumeMessage, ShutdownMessage,
                                      validate_json_message,
                                      validate_python_message)


def test_shutdown_command_parsing():
    m = validate_python_message({
        'type': 'SHUTDOWN' 
    })
    assert isinstance(m, ShutdownMessage)
    assert m.type == 'SHUTDOWN'

def test_resume_command_parsing():
    m = validate_python_message({
        'type': 'RESUME' 
    })
    assert isinstance(m, ResumeMessage)
    assert m.type == 'RESUME'

def test_heartbeat_command_parsing():
    m = validate_python_message({
        'type': 'HEARTBEAT',
        'version': '1.0.0'
    })
    assert isinstance(m, HeartbeatMessage)
    assert m.type == 'HEARTBEAT'
    assert m.version == '1.0.0'

def test_log_command_parsing():
    m = validate_python_message({
        'type': 'LOG',
        'level': 'info',
        'message': 'test_message'
    })
    assert isinstance(m, LogMessage)
    assert m.type == 'LOG'
    assert m.level == 'info'
    assert m.message == 'test_message'

def test_invalid_command_parsing():
    with pytest.raises(ValidationError):
        validate_python_message({
            'type': 'invalid_command'
        })

def test_json_parsing():
    m = validate_json_message('''
    {
        "type": "SHUTDOWN"
    }
    ''')
    assert isinstance(m, ShutdownMessage)
    assert m.type == 'SHUTDOWN'