from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import time
import MySQLdb as mdb

app = Flask(__name__)
socketio = SocketIO(app)

# MQTT 
mqtt_broker_address = "localhost"
mqtt_broker_port = 1883
mqtt_keypad_topic = "sensors/keypad"
mqtt_validation_topic = "sensors/validation"

# MQTT client
mqtt_client = mqtt.Client()
# Povezivanje na MySQL bazu podataka
con = mdb.connect('localhost', 'rpi6', 'raspberrypi6', 'sifre_korisnika')
cursor = con.cursor()

# Varijabla za pohranu trenutne šifre koju korisnik unosi
current_keypad_code = ""

# Callback funkcija MQTT
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(mqtt_keypad_topic)


def on_message(client, userdata, msg):
    global current_keypad_code
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    print(f"Received message on topic {topic}: {payload}")

    if topic == mqtt_keypad_topic:
        # Objavite šifru na MQTT temu kada korisnik pritisne tipku #
        if payload == "#":
            if current_keypad_code:
                mqtt_client.publish(mqtt_keypad_topic, current_keypad_code)
                current_keypad_code = ""  # Resetirajte trenutnu šifru nakon što je objavljena
            else:
                print("No keypad code entered")
        else:
            # Ažurirajte trenutnu šifru kada korisnik unese broj
            current_keypad_code += payload
    else:
        # Provjerite je li kod postoji u bazi podataka
        cursor.execute("SELECT username FROM keypad_data WHERE sifra = '{}'".format(payload))
        result = cursor.fetchone()
        if result:
            # Ako kod postoji, objavite korisničko ime zajedno s rezultatom validacije
            validation_result = result[0]
        else:
            validation_result = 0
        # Objavite rezultat validacije na MQTT temu
        mqtt_client.publish(mqtt_validation_topic, str(validation_result), "1")

# Postavljanje MQTT callback funkcija
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


mqtt_client.connect(mqtt_broker_address, mqtt_broker_port, 60)

mqtt_client.loop_start()

# Ruta
@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    print('Client connected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
