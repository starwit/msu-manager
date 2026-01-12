# MSU Manager User Manual
In this document, you'll find all information to run and to use MSU-Manager.

## Deployment
The following diagram shows a typical setup in conjunction with [Starwit's Awareness Engine](https://github.com/starwit/starwit-awareness-engine). MSU Manager is installed on a Linux computer that is used in an embedded scenario. Most important interaction happens with [Hardware Control Unit](https://github.com/starwit/msu-controller) which is a micro-controller based software, that turns embedded Linux computer on/off.

![](./img/deployment.drawio.svg)

## App Configuration

After installation config file of service is located at /etc/msu-manager/settings.yaml. Refer to the [settings template](../settings.template.yaml) for an example.

## OS Configuration
_This should have been set up by the installation script._
On Linux privilege to shutdown or reboot a computer is restricted (and for good reasons!). So it is necessary to provide a root-like access to shutdown for this service. In order to limit exposure of root privileges MSU Manager can only use shutdown. Here is an explanation, what APT install script is doing:

If you want to create the sudo policy manually, please refer to the [postinst script](../debian/preinst). \
Then use `sudo visudo -f /etc/sudoers.d/msu-manager` to create / edit the file.

## Managing the Service
To see if service is running use the following command:
```bash
systemctl status msu-manager
```

Please refer to SystemD documentation for more info, on how to use services, e.g. https://wiki.archlinux.org/title/Systemd

## Components

### HCU

#### Network Protocol
This application receives JSON messages from HCU (Hardware Control Unit) via serial communication. This is a micro controller based device, that manages power, temperature and a number of other physical aspects. Both application parts thus need to follow a shared protocol.

Protocol is composed of the following messages:

```json
{
    "type": "SHUTDOWN"
}

{
    "type": "RESUME"
}

{
    "type": "HEARTBEAT",
    "version" : "0.0.3"
}

{
    "type": "METRIC",
    "key": "temp0",
    "value": 0.123
}

{
    "type": "LOG",
    "level": "error",
    "message": "log message..."
}
```

#### Metrics
The application logs ignition state, heartbeat intervals and all logged metrics (like temperature or fan speed) and provides a Prometheus text format endpoint under `/api/metrics/`.