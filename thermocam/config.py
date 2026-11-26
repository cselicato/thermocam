from pathlib import Path
import tomllib

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _ROOT / "config.toml"
_EXAMPLE_PATH = _ROOT / "config.example.toml"

_DEFAULTS = {
    "server": "test.mosquitto.org",
    "port": 1883,
    "base_topic": "/singlecameras",
    "camera_number": 1,
}

_mqtt = dict(_DEFAULTS)
for _path in (_CONFIG_PATH, _EXAMPLE_PATH):
    if _path.is_file():
        with open(_path, "rb") as f:
            _mqtt.update(tomllib.load(f).get("mqtt", {}))
        break

MQTT_SERVER = _mqtt["server"]
MQTT_PORT = _mqtt.get("port", 1883)
CAMERA_NUMBER = _mqtt["camera_number"]
MQTT_PATH = f"{_mqtt['base_topic'].rstrip('/')}/camera{CAMERA_NUMBER}"