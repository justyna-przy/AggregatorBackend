from flask import Flask, jsonify, render_template, request

from config import MQTT_COMMAND_TOPIC
from mqtt_client import launch_mqtt_thread, latest_messages, publish_message

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/messages")
def api_messages():
    return jsonify(latest_messages())


@app.post("/api/emergency-stop")
def api_emergency_stop():
    data = request.get_json(silent=True) or {}
    payload = data.get("payload", "emergency_stop")
    ok = publish_message(payload)
    status = "sent" if ok else "failed"
    return jsonify({"status": status, "topic": MQTT_COMMAND_TOPIC, "payload": payload})


if __name__ == "__main__":
    launch_mqtt_thread()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
