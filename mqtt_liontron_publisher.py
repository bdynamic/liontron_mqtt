#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT publisher for Liontron BMS over BLE.

- Publishes auto-discovered sensors to Home Assistant
- Uses availability topic to indicate live/unavailable state
- Publishes 'online' on connect and 'offline' on clean or failed disconnect
"""

import os
import sys
import time
import json
import yaml
import signal
import logging
import paho.mqtt.client as mqtt
from liontron_battery import Battery

running = True
config = {}

def setup_logging(log_level="DEBUG"):
    """
    Set up logger with specified level.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    logging.basicConfig(level=numeric_level, format="%(asctime)s - %(levelname)s - %(message)s")

def load_config(path="config.yaml"):
    """
    Load YAML config from disk.
    """
    with open(path, "r") as f:
        return yaml.safe_load(f)

def build_discovery_payload(device_name, state_topic, name, availability_topic, unit=None):
    """
    Build a Home Assistant MQTT discovery payload.

    Args:
        device_name: The Home Assistant device identifier.
        state_topic: Topic where JSON payloads are published.
        name: Attribute name within JSON.
        availability_topic: Common LWT/status topic.
        unit: Optional unit of measurement.
    """
    payload = {
        "name": name,
        "state_topic": state_topic,
        "availability_topic": availability_topic,
        "payload_available": "online",
        "payload_not_available": "offline",
        "device": {
            "identifiers": [device_name],
            "name": device_name,
            "model": "Liontron BLE BMS",
            "manufacturer": "Liontron"
        },
        "unique_id": f"{device_name}_{name}",
        "object_id": f"{device_name}_{name}",
        "value_template": f"{{{{ value_json.{name} }}}}"
    }
    if unit:
        payload["unit_of_measurement"] = unit
    return payload

def publish_all(client, base_topic, device_name, data, retain=True):
    """
    Publish full state JSON and discovery configs.

    Args:
        client: MQTT client
        base_topic: Root topic
        device_name: Device ID used in topics
        data: Battery data
        retain: Retain flag
    """
    state_topic = f"{base_topic}/{device_name}/state"
    availability_topic = f"{base_topic}/status"

    # Publish main sensor values
    client.publish(state_topic, json.dumps(data), retain=retain)

    for key, value in data.items():
        if key in ["ProtectState", "Name"]:
            continue

        discovery_topic = f"homeassistant/sensor/{device_name}/{key}/config"

        # Infer unit
        unit = None
        if "Temp" in key:
            unit = "°C"
        elif "Vcell" in key or "Vmain" in key:
            unit = "V"
        elif "Imain" in key:
            unit = "A"
        elif "Ah" in key:
            unit = "Ah"
        elif key == "SoC":
            unit = "%"

        payload = build_discovery_payload(device_name, state_topic, key, availability_topic, unit)
        client.publish(discovery_topic, json.dumps(payload), retain=True)

def shutdown_handler(sig, frame):
    """
    Signal handler to publish 'offline' and exit cleanly.
    """
    global running
    logging.info(f"Signal {sig} received. Shutting down.")
    base_topic = config["mqtt"].get("base_topic", "liontron")
    client.publish(f"{base_topic}/status", "offline", retain=True)
    client.loop_stop()
    client.disconnect()
    running = False
    sys.exit(0)

def main():
    """
    Main script function. Connects MQTT, queries batteries, publishes data.
    """
    global running, client, config

    # Load config
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    config = load_config(config_file)
    setup_logging(config.get("log_level", "DEBUG"))

    vendor = config.get("vendor", "liontron")
    macs = config.get("batteries", [])
    update_interval = int(config.get("update_interval", 60))
    mqtt_cfg = config.get("mqtt", {})
    base_topic = mqtt_cfg.get("base_topic", "liontron")

    keepalive = int(update_interval * 2.5)

    # MQTT setup
    client = mqtt.Client()
    client.will_set(f"{base_topic}/status", "offline", retain=True)

    if mqtt_cfg.get("username") and mqtt_cfg.get("password"):
        client.username_pw_set(mqtt_cfg["username"], mqtt_cfg["password"])

    client.connect(mqtt_cfg.get("host", "localhost"), int(mqtt_cfg.get("port", 1883)), keepalive=keepalive)
    client.loop_start()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Publish LWT "online"
    client.publish(f"{base_topic}/status", "online", retain=True)

    try:
        while running:
            for mac in macs:
                try:
                    bms = Battery(mac)
                    data = bms.getBatteryload()
                    if "error" in data:
                        raise RuntimeError(data["error"])
                    name = data.get("Name", mac.replace(":", "").lower())
                    device_name = f"{vendor}_{name}"
                    logging.info(f"Publishing data for {device_name}")
                    publish_all(client, base_topic, device_name, data)
                except Exception as e:
                    logging.warning(f"Failed to read from {mac}: {e}")
            time.sleep(update_interval)
    except Exception as e:
        logging.error("Unhandled exception: %s", e)
        shutdown_handler("EXCEPTION", None)

if __name__ == "__main__":
    main()
