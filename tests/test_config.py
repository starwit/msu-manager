from msu_manager.config import MsuManagerConfig

def test_full_config():
    CONFIG = MsuManagerConfig.model_validate_json('''
    {
        "log_level": "INFO",
        "hcu_controller": {
            "enabled": true,
            "serial_device": "/dev/ttyUSB0",
            "serial_baud_rate": 9600,
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
        },
        "gps": {
            "enabled": true,
            "init_cmd": ["echo", "Initializing GPS"],
            "gpsd_host": "some_host",
            "gpsd_port": 2947
        },
        "frontend": {
            "enabled": true,
            "path": "custom_dist"
        }
    }
    ''')
    assert CONFIG.hcu_controller.serial_baud_rate == 9600
    assert CONFIG.uplink_monitor.check_interval_s == 10
    assert CONFIG.gps.gpsd_host == "some_host"
    assert CONFIG.frontend.path == "custom_dist"

def test_explicit_feature_disable():
    CONFIG = MsuManagerConfig.model_validate_json('''
    {
        "hcu_controller": {
            "enabled": false
        },
        "uplink_monitor": {
            "enabled": false
        },
        "gps": {
            "enabled": false
        },
        "frontend": {
            "enabled": false
        }
    }
    ''')
    assert CONFIG.hcu_controller.enabled == False
    assert CONFIG.uplink_monitor.enabled == False
    assert CONFIG.gps.enabled == False
    assert CONFIG.frontend.enabled == False

def test_implicit_feature_disable():
    CONFIG = MsuManagerConfig.model_validate_json('''
    { }
    ''')
    assert CONFIG.hcu_controller.enabled == False
    assert CONFIG.uplink_monitor.enabled == False
    assert CONFIG.gps.enabled == False
    assert CONFIG.frontend.enabled == False