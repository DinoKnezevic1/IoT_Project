#include <Keypad.h>
#include <Servo.h>
#include <PubSubClient.h>
#include <ESP8266WiFi.h>

#define ROW_NUM    4  
#define COLUMN_NUM 4  
#define SERVO_PIN  A0 
#define photoResistorPin 1 
const int LED_PIN = 13;
const int buzzer = 12;

char keys[ROW_NUM][COLUMN_NUM] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte pin_rows[ROW_NUM] = {D5, D6, D7, D8}; 
byte pin_column[COLUMN_NUM] = {D2, D3, D4, D0}; 

Servo servo; 
Keypad keypad = Keypad(makeKeymap(keys), pin_rows, pin_column, ROW_NUM, COLUMN_NUM);
String input_password;

int angle = 0; 
unsigned long lastTime;


const char* mqtt_server = "192.168.25.190"; 
const char* mqtt_topic = "sensors/validation";
const char* mqtt_keypad_topic = "sensors/keypad";

WiFiClient espClient;
PubSubClient client(espClient);

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  
  if (strcmp(topic, mqtt_topic) == 0) {
    if (strcmp((char*)payload, "1") == 0) {
      angle = 90;
      servo.write(angle);
      lastTime = millis();
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("arduinoClient")) {
      Serial.println("connected");
      client.subscribe(mqtt_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(9600); 
  pinMode(buzzer, OUTPUT);
  pinMode(LED_PIN, OUTPUT); 
  input_password.reserve(8); 
  servo.attach(SERVO_PIN);
  servo.write(0); 
  lastTime = millis();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  char key = keypad.getKey();

  if (key) {
    if (key == '*') {
      input_password = ""; 
    } else if (key == '#') {
      client.publish(mqtt_keypad_topic, input_password.c_str());
      Serial.println("Published password: " + input_password);
      input_password = ""; 
    } else {
      input_password += key; 
    }
  }

  if (angle == 90 && (millis() - lastTime) > 60000) { 
    angle = 0;
    servo.write(angle);
  }
}
