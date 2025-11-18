# Power Toggle Service User's Manual
In this document, you'll find all information to run and to use MSU-Manager.

## Deployment
The following diagram shows a typical setup in conjunction with [Starwit's Awareness Engine](https://github.com/starwit/starwit-awareness-engine). MSU Manager is installed on a Linux computer that is used in an embedded scenario. Most important interaction happens with [Hardware Control Unit](https://github.com/starwit/msu-controller) which is a micro-controller based software, that turns embedded Linux computer on/off.

![](./img/deployment.drawio.svg)

## App Configuration

After installation config file of service is located at /etc/msu-manager/settings.yaml. Here is an example of configuration file:

```yaml
log_level: INFO
hcu_controller:
  enabled: true
  udp_bind_address: 0.0.0.0                                                         # bind address for shutdown service
  udp_listen_port: 8001
  shutdown_delay_s: 180                                                             # Delay after having received SHUTDOWN command to executing shutdown (in seconds)
  shutdown_command: ['sudo', 'shutdown', '-h', 'now']                               # Don't accidentally shut down your computer and use a dummy command like "touch /tmp/shutdown_called" for testing
uplink_monitor:
  enabled: true
  restore_connection_cmd: ["sudo", "/usr/bin/bash", "/usr/bin/lte-connect.sh"]      # Command to restore the connection (use a dummy command like "touch /tmp/restore_called" for testing)
  wwan_device: 'wwan0'                                                              # WWAN interface name (see mmcli -m any and check System.ports, it's probably wwan0)
  wwan_usb_id: '1234:5678'                                                          # USB device ID of the WWAN modem (see lsusb)
  wwan_apn: 'test.apn'                                                              # APN to use for the WWAN connection
  check_connection_target: '1.1.1.1'                                                # Target to ping for connection checks
  check_connection_device: 'wwan0'                                                  # Device to use for connection checks (should mostly be the same as wwan_device, null/unset means any uplink will do)
  check_interval_s: 10

```
## OS Configuration
_This should have been set up by the installation script._
On Linux privilege to shutdown or reboot a computer is restricted (and for good reasons!). So it is necessary to provide a root-like access to shutdown for this service. In order to limit exposure of root privileges MSU Manager can only use shutdown. Here is an explanation, what APT install script is doing:

```
sudo visudo -f /etc/sudoers.d/msu-manager
# Add the following line
# msumanager ALL=NOPASSWD: /usr/sbin/shutdown -h now
```

## Managing the Service
To see if service is running use the following command:
```bash
systemctl status msu-manager
```

Please refer to SystemD documentation for more info, on how to use services, e.g. https://wiki.archlinux.org/title/Systemd

## Network Protocol
This application receives UDP messages from HCU (Hardware Control Unit). This is a micro controller based device, that manages power, temperature and a number of other physical aspects. Both application parts thus need to follow a shared protocol.

Protocol is composed of the following messages:

```json
{
    "command": "SHUTDOWN"
}

{
    "command": "RESUME"
}

{
    "command": "HEARTBEAT",
    "version" : "0.0.3"
}

{
    "command": "LOG",
    "key": "key",
    "value": "value"
}
```
