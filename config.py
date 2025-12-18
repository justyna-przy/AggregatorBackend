import os

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "alderaan.software-engineering.ie")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_EVENT_TOPIC = os.getenv("MQTT_EVENT_TOPIC", "computor/esp32/events")
MQTT_COMMAND_TOPIC = os.getenv("MQTT_COMMAND_TOPIC", "computor/esp32/cmd")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "10"))

# Database Configuration
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///elevator_data.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
