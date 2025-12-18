import json

from flask import Flask, Response, jsonify, render_template, request

from config import MQTT_COMMAND_TOPIC, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from mqtt_client import (
    launch_mqtt_thread,
    latest_messages,
    publish_message,
    subscribe_to_messages,
    unsubscribe,
)
from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

db.init_app(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/messages")
def api_messages():
    return jsonify(latest_messages())


@app.post("/api/command")
def api_command():
    data = request.get_json(silent=True) or {}
    payload = data.get("payload", "")
    if not payload:
        return jsonify({"status": "error", "message": "No payload provided"}), 400
    ok = publish_message(payload)
    status = "sent" if ok else "failed"
    return jsonify({"status": status, "topic": MQTT_COMMAND_TOPIC, "payload": payload})


@app.route("/api/events/stream")
def api_events_stream():
    """Server-Sent Events endpoint for real-time message streaming."""
    def generate():
        q = subscribe_to_messages()
        try:
            while True:
                message = q.get()
                yield f"data: {json.dumps(message)}\n\n"
        except GeneratorExit:
            unsubscribe(q)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    launch_mqtt_thread()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
