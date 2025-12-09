# MSU Manager Service
This components manages various aspects for Mobilytix Sensoring Units among which are power and thermal management.\
One of its core features is receiving commands from the [HCU (Hardware Control Unit)](https://github.com/starwit/msu-controller). It is shipped for Debian based Linux distributions and is tested with Ubuntu. 

## Local Development
App consists of two parts: Python backend and React frontend.

### Build Frontend
Copy settings template in a new file and configure frontend values like so:
```yaml
frontend:
  enabled: true
  path: 'frontend/dist'
```
Then run in folder frontend:
```bash
npm install
npm run build
```

### Run backend
To run the application manually you can use Poetry:
```bash
poetry install
poetry run fastapi run msu_manager/main.py
```

Application will serve frontend under: http://localhost:8000. If you run npm start in frontend folder, you let npm compile React code on the fly.

## Usage

Service is shipped as APT package, see [release](https://github.com/starwit/msu-manager/releases) page to download latest package. How to configure and use service see [manual](doc/MANUAL.md).

## Build

Here are all necessarey information for developers, to build and run service.

### Prerequisites
Things you need to build package.

* Python 
* Poetry
* build-essentials
* npm

### Build APT package
Makefile has target to build an APT package. Virtual environment is created by exporting Poetry dependencies into a requirements.txt file. APT is build like so:
```bash
poetry self add poetry-plugin-export
make build-deb
```

APT package can then be found in folder _target_. You can test installation using Docker, however SystemD (probably) won't work.
```bash
docker run -it --rm -v ./target:/app  jrei/systemd-ubuntu:latest bash
apt update && apt install -y /app/msu-manager_0.0.7_all.deb
```
You can however test, if everything is installed to the right place. If you want to test service use the following examples:
```bash
echo -n '{"command": "HEARTBEAT","version" : "0.0.3"}' | nc -4u -q1 localhost 5151
echo -n '{"command": "LOG", "key": "temperature", "value": "42.0"}' | nc -4u -q1 localhost 5151
echo -n '{"command": "SHUTDOWN"}' | nc -4u -q1 localhost 5151
echo -n '{"command": "RESUME"}' | nc -4u -q1 localhost 5151
```
