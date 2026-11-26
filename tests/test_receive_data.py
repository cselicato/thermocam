"""
Test script receive_data.py

Usage: run this script and then run receive_data to visually check
it plots what expected
"""

import time
import numpy as np
import paho.mqtt.client as mqtt
from loguru import logger

from thermocam.config import MQTT_SERVER, MQTT_PORT, MQTT_PATH

class DummyCamera:
    """
    Object to generate and publish data that mimics what the AtomS3 publishes
    """

    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.connect(MQTT_SERVER, MQTT_PORT, 60)

    def pixel_data(self):
        """ Publish pixel data
        """
        self.client.publish(f"{MQTT_PATH}/pixels/data", "1 2 3.00,4 5 6.00")

    def area_data(self):
        """ Publish area data
        """
        self.client.publish(f"{MQTT_PATH}/area/data",
                            "max: 10 min: 9 avg: 8 x: 7 y: 6 w: 5 h: 4")

    def image(self):
        """ Publish image
        """
        # generate random image
        values = np.random.rand((32*24))*30
        values = np.float32(values)
        img = values.tobytes()
        self.client.publish(f"{MQTT_PATH}/image", img)

    def empty(self):
        """Publish empty message
        """
        self.client.publish(f"{MQTT_PATH}/image", "")


def manual_test_loop():
    """Start a publishing loop

    Publishes dummy data every 0.5 seconds
    """

    camera = DummyCamera()

    logger.info("Starting dummy camera publish loop. Press CTRL+C to stop.")
    try:
        while True:
            time.sleep(0.5)
            camera.pixel_data()
            camera.area_data()
            camera.image()
    except KeyboardInterrupt:
        logger.info("Stopped by user.")


if __name__ == "__main__":
    manual_test_loop()
