import os
from enum import Enum
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from pydantic_settings import (BaseSettings, SettingsConfigDict,
                               YamlConfigSettingsSource)


class LogLevel(str, Enum):
    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'
    WARNING = 'WARNING'
    INFO = 'INFO'
    DEBUG = 'DEBUG'


class UplinkMonitorConfig(BaseModel):
    enabled: Literal[True]
    restore_connection_cmd: List[str]
    wwan_device: str
    wwan_apn: str
    check_connection_target: str
    check_connection_device: str = None
    check_interval_s: int = 10


class UplinkMonitorConfigDisabled(BaseModel):
    enabled: Literal[False] = False


class HcuControllerConfig(BaseModel):
    enabled: Literal[True]
    serial_device: Path
    serial_baud_rate: int
    shutdown_delay_s: int = 180
    shutdown_command: List[str]


class HcuControllerConfigDisabled(BaseModel):
    enabled: Literal[False] = False


class FrontendConfig(BaseModel):
    enabled: Literal[True]
    path: str = 'dist'


class FrontendConfigDisabled(BaseModel):
    enabled: Literal[False] = False


class GpsConfig(BaseModel):
    enabled: Literal[True]
    init_cmd: Optional[List[str]] = None
    gpsd_host: str = '127.0.0.1'
    gpsd_port: int = 2947
    

class GpsConfigDisabled(BaseModel):
    enabled: Literal[False] = False


class MsuManagerConfig(BaseSettings):
    log_level: LogLevel = LogLevel.INFO
    hcu_controller: HcuControllerConfig | HcuControllerConfigDisabled = Field(discriminator='enabled', default=HcuControllerConfigDisabled())
    uplink_monitor: UplinkMonitorConfig | UplinkMonitorConfigDisabled = Field(discriminator='enabled', default=UplinkMonitorConfigDisabled())
    frontend: FrontendConfig | FrontendConfigDisabled = Field(discriminator='enabled', default=FrontendConfigDisabled())
    gps: GpsConfig | GpsConfigDisabled = Field(discriminator='enabled', default=GpsConfigDisabled())


    model_config = SettingsConfigDict(env_nested_delimiter='__')

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        YAML_LOCATION = os.environ.get('SETTINGS_FILE', 'settings.yaml')
        return (init_settings, env_settings, YamlConfigSettingsSource(settings_cls, yaml_file=YAML_LOCATION), file_secret_settings)