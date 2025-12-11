import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "alderaan.software-engineering.ie")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "elevator/test/events")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "aggregator-backend")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "10"))
