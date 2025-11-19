from msu_manager.config import MsuManagerConfig

def test_full_config(monkeypatch):
    CONFIG = MsuManagerConfig.model_validate_json('''
    {
        "log_level": "INFO",
        "hcu_controller": {
            "enabled": true,
            "udp_bind_address": "0.0.0.0",
            "udp_listen_port": 8001,
            "shutdown_delay_s": 180,
            "shutdown_command": ["touch", "/tmp/shutdown_executed"]
        },
        "uplink_monitor": {
            "enabled": true,
            "restore_connection_cmd": ["echo", "Restoring connection"],
            "wwan_device": "test_wwan",
            "wwan_apn": "test_apn",
            "check_connection_target": "1.1.1.1",
            "check_connection_device": "eth0",
            "check_interval_s": 10
        }
    }
    ''')
    assert CONFIG.hcu_controller.udp_listen_port == 8001
    assert CONFIG.uplink_monitor.check_interval_s == 10

def test_explicit_feature_disable():
    CONFIG = MsuManagerConfig.model_validate_json('''
    {
        "hcu_controller": {
            "enabled": false
        },
        "uplink_monitor": {
            "enabled": false
        }
    }
    ''')
    assert CONFIG.hcu_controller.enabled == False
    assert CONFIG.uplink_monitor.enabled == False

def test_implicit_feature_disable(monkeypatch):
    CONFIG = MsuManagerConfig.model_validate_json('''
    { }
    ''')
    assert CONFIG.hcu_controller.enabled == False
    assert CONFIG.uplink_monitor.enabled == False