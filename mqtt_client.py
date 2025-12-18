import threading
from datetime import datetime, timezone
from queue import Queue
from typing import Any, Dict, List

from flask import Flask

import paho.mqtt.client as mqtt

from config import (
    MAX_MESSAGES,
    MQTT_BROKER,
    MQTT_COMMAND_TOPIC,
    MQTT_PORT,
    MQTT_EVENT_TOPIC,
)
from models import EVENT_TYPES, Event, EventType, db

_latest_messages: List[Dict[str, Any]] = []
_message_lock = threading.Lock()
_message_id_counter = 0
_client: mqtt.Client | None = None
_subscribers: List[Queue] = []
_subscribers_lock = threading.Lock()
_flask_app: Flask | None = None


def subscribe_to_messages() -> Queue:
    """Subscribe to new messages. Returns a queue that receives new messages."""
    q: Queue = Queue()
    with _subscribers_lock:
        _subscribers.append(q)
    return q


def unsubscribe(q: Queue):
    """Unsubscribe from messages."""
    with _subscribers_lock:
        if q in _subscribers:
            _subscribers.remove(q)


def _notify_subscribers(message: Dict[str, Any]):
    """Notify all subscribers of a new message."""
    with _subscribers_lock:
        for q in _subscribers:
            q.put(message)


def register_flask_app(app: Flask):
    """Provide Flask app so the MQTT thread can open app contexts for DB writes."""
    global _flask_app
    _flask_app = app


def _extract_floor(event_type: str) -> int | None:
    if event_type.startswith("stopped_at_floor_"):
        try:
            return int(event_type.rsplit("_", 1)[-1])
        except ValueError:
            return None
    if event_type.startswith("cabin_button_"):
        try:
            return int(event_type.rsplit("_", 1)[-1])
        except ValueError:
            return None
    if event_type.startswith("call_button_"):
        tail = event_type[len("call_button_") :]
        parts = tail.split("_", 1)
        if parts and parts[0].isdigit():
            return int(parts[0])
    return None


def _persist_event(message: Dict[str, Any]):
    """Persist the MQTT message into the database using the payload as event_type."""
    if _flask_app is None:
        return

    payload = message.get("payload")
    if not payload or payload not in EVENT_TYPES:
        return

    ts_str = message.get("timestamp")
    ts = None
    if ts_str:
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            ts = None

    floor = _extract_floor(payload)

    try:
        with _flask_app.app_context():
            event_type_row = EventType.query.filter_by(event_type=payload).first()
            if event_type_row is None:
                return
            event = Event(event_type_id=event_type_row.id, floor=floor)
            if ts is not None:
                event.timestamp = ts
            db.session.add(event)
            db.session.commit()
    except Exception as exc:  # pragma: no cover - defensive logging
        # Avoid crashing the MQTT thread if DB is unavailable.
        try:
            db.session.rollback()
        except Exception:
            pass
        print(f"[MQTT][DB] Failed to persist event '{payload}': {exc}")


def on_mqtt_connect(client: mqtt.Client, userdata=None, flags=None, reason_code=0, properties=None):
    print(f"[MQTT] Connected and subscribing to {MQTT_EVENT_TOPIC}")
    client.subscribe(MQTT_EVENT_TOPIC)


def on_mqtt_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    global _message_id_counter
    payload = msg.payload.decode("utf-8", errors="replace")
    print(f"[MQTT] {msg.topic}: {payload}")

    with _message_lock:
        _message_id_counter += 1
        message = {
            "id": _message_id_counter,
            "topic": msg.topic,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _latest_messages.append(message)
        del _latest_messages[:-MAX_MESSAGES]

    _persist_event(message)
    _notify_subscribers(message)
    print(f"[MQTT] Stored message #{message['id']}. Total buffered: {len(_latest_messages)}")


def start_mqtt_loop():
    global _client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
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
    with _message_lock:
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
