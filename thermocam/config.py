from pathlib import Path
import tomllib

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"

with open(_CONFIG_PATH, "rb") as f:
    _cfg = tomllib.load(f)

_mqtt = _cfg["mqtt"]

MQTT_SERVER = _mqtt["server"]
MQTT_PORT = _mqtt.get("port", 1883)
CAMERA_NUMBER = _mqtt["camera_number"]
MQTT_PATH = f"{_mqtt['base_topic'].rstrip('/')}/camera{CAMERA_NUMBER}"