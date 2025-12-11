import json
import threading

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template

from config import (
    MAX_MESSAGES,
    MQTT_BROKER,
    MQTT_CLIENT_ID,
    MQTT_PORT,
    MQTT_TOPIC,
)

latest_messages: list[dict[str, str]] = []

app = Flask(__name__)


def on_mqtt_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
    print(f"[MQTT] Connected with code {reason_code}, subscribing to {MQTT_TOPIC}")
    client.subscribe(MQTT_TOPIC)


def on_mqtt_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    payload = msg.payload.decode("utf-8", errors="replace")
    print(f"[MQTT] {msg.topic}: {payload}")
    try:
        json.loads(payload)
    except json.JSONDecodeError:
        pass

    latest_messages.append(
        {
            "topic": msg.topic,
            "payload": payload,
        }
    )
    del latest_messages[:-MAX_MESSAGES]
    print(f"[MQTT] Stored message. Total buffered: {len(latest_messages)}")


def start_mqtt_loop():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    print(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT}")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()


def launch_mqtt_thread():
    t = threading.Thread(target=start_mqtt_loop, daemon=True)
    t.start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/messages")
def api_messages():
    return jsonify(list(reversed(latest_messages)))


if __name__ == "__main__":
    launch_mqtt_thread()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
