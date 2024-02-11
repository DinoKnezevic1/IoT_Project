from flask import Flask, render_template
from flask_socketio import SocketIO
import json
import paho.mqtt.client as mqtt
import time
import MySQLdb as mdb

app = Flask(__name__)
socketio = SocketIO(app)

# MQTT settings
mqtt_broker_address = "localhost"
mqtt_broker_port = 1883
mqtt_topics = ["sensors/keypad"]

# Initialize MQTT client
mqtt_client = mqtt.Client()
con = mdb.connect('localhost', 'sensor_writer', 'password', 'projekt')
cursor = con.cursor()

# Define callback functions for MQTT
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    for topic in mqtt_topics:
        client.subscribe(topic)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    print(f"Received message on topic {topic}: {payload}")
    # Emit the message to all connected WebSocket clients
    socketio.emit("mqtt_message", {"topic": topic, "message": payload})

    if topic == "sensors/keypad":
        # Insert data into the database
        sql = "INSERT INTO sensorData(datum, vrijeme, sifra) VALUES ('%s', '%s', '%s')" % (time.strftime("%Y-%m-%d"), time.strftime("%H:%M:%S"), payload)
        cursor.execute(sql)
        con.commit()

# Set MQTT callback functions
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to MQTT broker
mqtt_client.connect(mqtt_broker_address, mqtt_broker_port, 60)

mqtt_client.loop_start()

# Define the route for the HTML page
@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    print('Client connected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
