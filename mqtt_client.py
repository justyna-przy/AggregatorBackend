import json
import threading
from typing import Any, Dict, List

import paho.mqtt.client as mqtt

from config import (
    MAX_MESSAGES,
    MQTT_BROKER,
    MQTT_CLIENT_ID,
    MQTT_COMMAND_TOPIC,
    MQTT_PORT,
    MQTT_EVENT_TOPIC,
)

_latest_messages: List[Dict[str, Any]] = []
_client: mqtt.Client | None = None


def on_mqtt_connect(client: mqtt.Client, userdata=None, flags=None, reason_code=0, properties=None):
    print(f"[MQTT] Connected and subscribing to {MQTT_EVENT_TOPIC}")
    client.subscribe(MQTT_EVENT_TOPIC)


def on_mqtt_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    payload = msg.payload.decode("utf-8", errors="replace")
    print(f"[MQTT] {msg.topic}: {payload}")
    try:
        json.loads(payload)
    except json.JSONDecodeError:
        pass

    _latest_messages.append({"topic": msg.topic, "payload": payload})
    del _latest_messages[:-MAX_MESSAGES]
    print(f"[MQTT] Stored message. Total buffered: {len(_latest_messages)}")


def start_mqtt_loop():
    global _client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    print(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT}")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    _client = client
    client.loop_forever()


def launch_mqtt_thread():
    t = threading.Thread(target=start_mqtt_loop, daemon=True)
    t.start()


def latest_messages() -> list[dict[str, Any]]:
    return list(reversed(_latest_messages))


def publish_message(
    payload: str,
    topic: str | None = None,
    qos: int = 0,
    retain: bool = False,
) -> bool:
    """Publish a message on the MQTT broker. Returns True if queued to send."""
    if topic is None:
        topic = MQTT_COMMAND_TOPIC
    if _client is None:
        print("[MQTT] Publish failed: client not connected yet")
        return False
    result = _client.publish(topic, payload=payload, qos=qos, retain=retain)
    ok = result.rc == mqtt.MQTT_ERR_SUCCESS
    print(f"[MQTT] Publish to {topic}: {payload} (ok={ok})")
    return ok
