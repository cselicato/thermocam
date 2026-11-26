# thermocam

Thermocam receives thermal frames from an M5Stack AtomS3 equipped with an MLX90640 infrared sensor and publishes/receives camera data through MQTT. The Python application displays a 32 × 24 thermal image, live temperatures for selected pixels and a rectangular area, device status, and controls for camera settings.

## Repository layout

- `thermocam/` — Python visualization and MQTT package.
  - `handler.py` — connects MQTT messages to GUI components and output files.
  - `visualization.py` — thermal image and live plots.
  - `callbacks.py` — mouse, button, and MQTT callbacks.
  - `settings.py` — camera settings and control panel.
  - `roi.py` — single-pixel and rectangular-area selections.
  - `videomaker.py` — MP4 video recording.
  - `config.py` — loads `config.toml`.
- `scripts/receive_data.py` — starts the visualization application.
- `scripts/send_settings.py` — changes camera settings from the terminal.
- `therm_atom/` — Arduino sketch and MLX90640/I²C support files for the AtomS3.
- `tests/` — package tests.
- `docs/` — generated and source Sphinx documentation.
- `config.toml` — active MQTT configuration.
- `config_template.toml` — copy used for a new configuration.

## Requirements

### Hardware

- M5Stack AtomS3
- MLX90640 infrared thermal sensor
- I²C/Grove wiring compatible with the AtomS3 sketch
- Wi-Fi network
- An MQTT broker reachable from both the computer and the AtomS3

The sketch initializes I²C on GPIO 2 (SDA) and GPIO 1 (SCL), so the sensor must be connected to the corresponding Grove/I²C pins.

### Python

Python 3.11 or newer is recommended. The package dependencies are:

- NumPy
- Matplotlib
- OpenCV
- Paho MQTT
- Loguru

### Arduino firmware

Use Arduino IDE or Arduino CLI with ESP32 board support and install these libraries:

- `M5Unified`
- `PubSubClient`
- `WiFiManager`
- `Preferences` and `SPIFFS` (provided by the ESP32 core)

The `MLX90640_API` and I²C driver sources are already included in `therm_atom/`.

## 1. Configure and flash the AtomS3

1. Open `therm_atom/therm_atom.ino` in Arduino IDE.
2. Select the AtomS3/ESP32 board and the appropriate serial port.
3. Install the libraries listed above and compile/upload the sketch.
4. Hold the AtomS3 button while the board boots to force the setup portal immediately. Otherwise, the sketch will open `AtomS3-Cam-Setup` automatically if it cannot connect with stored credentials.
5. Join the `AtomS3-Cam-Setup` Wi-Fi access point and open `192.168.4.1` in a browser.
6. Enter:
   - Wi-Fi SSID and password;
   - MQTT broker address, such as `test.mosquitto.org`; and
   - a camera number, such as `1`.

The broker address and camera number are stored in the AtomS3 NVS/Preferences. After initial setup, you can also hold the button during boot to change them. The sketch uses an unencrypted MQTT connection on TCP port 1883.

For a private broker, make sure it is reachable from the AtomS3 network and that credentials, TLS, or a different port are supported/configured before deployment. The public broker in the default configuration requires no authentication and is intended for testing.

## 2. Install the Python application

Run these commands from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

Alternatively, install the listed dependencies directly:

```bash
pip install -r requirements.txt
```

Use a Matplotlib backend that supports interactive windows. The default desktop backend is normally appropriate on Linux. If GUI windows do not appear or a backend error is reported, set an interactive backend before starting, for example:

```bash
export MPLBACKEND=TkAgg
```

## 3. Configure the Python MQTT topic

Edit `config.toml`:

```toml
[mqtt]
server = "test.mosquitto.org"
port = 1883
base_topic = "/singlecameras"
camera_number = 1
```

The active Python and firmware camera numbers must match. For `camera_number = 1`, all topics are based on:

```text
/singlecameras/camera1
```

A different camera number creates a separate topic namespace, allowing multiple cameras to operate behind the same broker.

`config_template.toml` contains a clean starting example. Create or restore the active file with:

```bash
cp config_template.toml config.toml
```

Then change `server`, `port`, `base_topic`, and `camera_number` as needed. Restart the Python application after changing `config.toml`.

## 4. Start visualization

With the AtomS3 running and the virtual environment active:

```bash
python scripts/receive_data.py
```

The receiver subscribes to the selected camera namespace, requests the current persistent state, and opens:

- a thermal-image window; and
- a control panel.

To create timestamped text files for pixel and area measurements at every received sample:

```bash
python scripts/receive_data.py --save y
```

The default is `--save n`. Save files are written to `~/thermocam_out/data/`.

## Using the visualization

### Thermal image

The left panel shows the latest MLX90640 frame. The image is a 32 × 24 array published as 768 little-endian `float32` temperatures. The color scale is refreshed approximately every ten frames and includes 10% padding around the measured minimum and maximum.

The status in the control panel is **ONLINE** when an image has arrived within the last two seconds and **OFFLINE** otherwise.

### Individual pixels

With **Select area** unchecked, click anywhere inside the thermal-image axes to add a pixel. The coordinate is sent to the AtomS3, which stores it and publishes temperatures on:

```text
/singlecameras/camera1/pixels/data
```

The right-hand upper plot shows temperature history for each selected pixel. Clicking an already selected pixel does not add a duplicate.

### Rectangular area

Check **Select area** and click two opposite corners in the thermal-image axes:

1. First click sets the first corner.
2. Second click defines the rectangle and publishes it.
3. A third click clears the pending corner display and allows a new area to be started.

The area is sent as `x_left y_low width height`. The AtomS3 publishes maximum, minimum, and average temperatures on:

```text
/singlecameras/camera1/area/data
```

The lower plot shows all three temperature values over time. The control panel **Reset area** button clears the current area on the device and in the application.

### Video recording

Check **Video** in the visualization window to begin recording. Check it again to stop and finalize the file. Videos are stored as timestamped MP4 files in `~/thermocam_out/videos/` and use 4 fps and 720 × 960 output dimensions.

### Saved data

With `--save y`, the application creates two timestamped files:

- `pix_YYYYMMDD_HHMMSS.txt` — timestamp and the latest temperature for each selected pixel;
- `area_YYYYMMDD_HHMMSS.txt` — timestamp, rectangle coordinates, average, minimum, and maximum temperatures.

The files remain open while the application runs and are closed on shutdown.

## Camera settings

### From the control panel

The control panel provides:

- **Rate [Hz]**: 0.5, 1, 2, 4, or 8 Hz.
- **Shift**: reflected-temperature compensation. The default is `8`.
- **Emis.**: emissivity in the range `0 < emissivity <= 1`. The default is `0.95`.
- **Readout mode**: Chess pattern or TV interleave.

Enter a shift or emissivity value and press Enter in the text box. Click **APPLY** to publish the pending values. **DEFAULT** restores and publishes `2 Hz`, shift `8`, emissivity `0.95`, and Chess mode.

The settings payload uses the format required by the firmware: refresh-rate exponent, shift, emissivity, and mode. Each line is a separate newline. The AtomS3 writes it to SPIFFS and reboots before initializing the MLX90640.

Use **Request info** or wait for startup to receive the latest settings, pixels, and area. Broker-retained messages may be unavailable after a disconnect, so this request is useful for refreshing the GUI state.

**Reset pixels** removes all selected pixels from the AtomS3 and SPIFFS.

### From the terminal

Send settings without opening the visualization:

```bash
python scripts/send_settings.py \
  --rate 4 \
  --shift 8 \
  --emissivity 0.95 \
  --mode 0
```

Supported options:

```text
--rate {0.5,1,2,4,8}
--shift FLOAT
--emissivity FLOAT   # 0 < value <= 1
--mode {0,1}         # 0 = Chess, 1 = TV interleave
```

Defaults are `2 Hz`, shift `8`, emissivity `0.95`, and mode `0`. The script prints published status through Loguru and waits for Paho MQTT to complete publication.

View command help with:

```bash
python scripts/send_settings.py --help
```

## MQTT interface

All topic names below are relative to `/singlecameras/cameraN`.

| Topic suffix | Direction | Purpose |
|---|---|---|
| `/image` | AtomS3 → receiver | 768 binary `float32` temperature values |
| `/pixels/coord` | Receiver → AtomS3 | Add pixel as `x y` |
| `/pixels/reset` | Receiver → AtomS3 | Clear all pixels |
| `/pixels/current` | AtomS3 → receiver | Retained comma-separated pixel coordinates or `none` |
| `/pixels/data` | AtomS3 → receiver | Pixel temperatures as `x y temperature` entries |
| `/area` | Receiver → AtomS3 | Set area as `x_left y_low width height` |
| `/area/reset` | Receiver → AtomS3 | Clear the area |
| `/area/current` | AtomS3 → receiver | Retained area coordinates or `none` |
| `/area/data` | AtomS3 → receiver | Area maximum, minimum, average, and coordinates |
| `/settings` | Receiver → AtomS3 | Camera settings with newline-separated fields |
| `/settings/current` | AtomS3 → receiver | Retained human-readable settings |
| `/info_request` | Receiver → AtomS3 | Request settings and ROI state |
| `/check` | AtomS3 → receiver | Image publication acknowledgment |
| `/temps` | AtomS3 → receiver | Whole-frame JSON min/max/average |
| `/pixels/connected` | AtomS3 → broker | Per-loop connectivity heartbeat payload |

The receiver subscribes to `<base_topic>/cameraN/#`, so the broker and topic namespace must match the firmware configuration.

## Persistent device state

The AtomS3 stores data in SPIFFS and ESP32 Preferences:

- `/M5Stack/cam_settings.txt` — refresh-rate setting, shift, emissivity, and readout mode;
- `/M5Stack/pixels.txt` — saved pixel coordinates;
- `/M5Stack/area.txt` — saved area coordinates;
- ESP32 Preferences — Wi-Fi, MQTT broker, and camera number data.

Selecting a new setting causes an ESP32 restart. Pixel and area selections are restored when the device boots.

## Troubleshooting

- **No image is displayed:** confirm the broker address and camera number match in `config.toml` and on the AtomS3; check that the device is online and subscribed; verify broker port 1883 is reachable.
- **Control panel says OFFLINE:** wait for frames from `/image`. Also verify network and broker connectivity.
- **Wi-Fi or MQTT setup cannot be opened:** hold the AtomS3 button for the first 1.5 seconds after boot to force the setup portal.
- **Invalid MQTT image:** the receiver expects exactly 768 binary `float32` values, 3072 bytes total.
- **I²C/sensor failure:** verify sensor power and I²C wiring and confirm SDA/SCL are GPIO 2/1. Use Serial Monitor at 115200 baud for firmware diagnostics.
- **GUI files are not created:** run `--save y` and ensure `~/thermocam_out/data/` is writable.
- **Paho MQTT API errors:** the scripts use Paho callback API version 2. A Paho version compatible with `CallbackAPIVersion.VERSION2` is required.
- **Public broker delays or missing retained state:** use a local broker or broker with predictable service for reliable testing. The public broker is unauthenticated and not suitable for sensitive data.

## Development

Generated API documentation is available under `docs/build/html/`; source documentation is under `docs/source/`.
