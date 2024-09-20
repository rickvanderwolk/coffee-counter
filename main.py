import json
import paho.mqtt.client as mqtt
from decimal import Decimal
import time
import csv
import os
import joblib
import numpy as np
import pandas as pd
import subprocess

MQTT_BROKER_ADDRESS = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "shellyplusplugs-c82e1806b8a0/status/switch:0"
LOG_FILE_PATH = 'power_log.csv'
COUNTER_FILE_PATH = 'coffee_counter.txt'

model = joblib.load('coffee_model.pkl')

event_buffer = []
prediction_buffer = []

coffee_count = 0
last_detection_time = 0

def print_log(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def initialize_log_file():
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'power', 'coffee_brewed'])
        print_log(f"Log file {LOG_FILE_PATH} initialized with headers.")

def initialize_counter_file():
    global coffee_count
    if not os.path.exists(COUNTER_FILE_PATH):
        with open(COUNTER_FILE_PATH, 'w') as file:
            file.write('0')
        coffee_count = 0
    else:
        with open(COUNTER_FILE_PATH, 'r') as file:
            coffee_count = int(file.read().strip())
    print_log(f"Coffee counter initialized with count: {coffee_count}")

def update_counter_file():
    global coffee_count
    with open(COUNTER_FILE_PATH, 'w') as file:
        file.write(str(coffee_count))
    print_log(f"Coffee counter updated to: {coffee_count}")

    try:
        subprocess.run(
            ['bash', 'send_message.sh', f'{{"type":"coffee","body":{coffee_count}}}'],
            check=True
        )
        subprocess.run(
            ['bash', 'send_message.sh', f'{{"type":"chat","body":"☕️ Kopje koffie gezet"}}'],
            check=True
        )
        print_log("Message sent successfully.")
    except subprocess.CalledProcessError as e:
        print_log(f"Failed to send message: {e}")

def log_power_data(timestamp, power):
    with open(LOG_FILE_PATH, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, power, 'undefined'])

def predict_coffee():
    global coffee_count, prediction_buffer, last_detection_time

    if len(event_buffer) == 15:
        mean_last_15 = np.mean(event_buffer)
        max_last_15 = np.max(event_buffer)
        min_last_15 = np.min(event_buffer)

        X = pd.DataFrame([[event_buffer[-1], mean_last_15, max_last_15, min_last_15]],
                         columns=['power', 'mean_last_15', 'max_last_15', 'min_last_15'])

        prediction = model.predict(X)
        probability = model.predict_proba(X)[:, 1].mean()

        current_time = time.time()
        if probability > 0.5:
            print_log(f"Predicted: Coffee is being brewed with probability {probability:.2f}")
            if last_detection_time == 0:
                last_detection_time = current_time
                print_log("Timer started.")
            prediction_buffer.append((current_time, probability))
        else:
            print_log(f"Predicted: No coffee brewing detected with probability {probability:.2f}")
            if last_detection_time > 0:
                elapsed_time = current_time - last_detection_time
                mean_probability = np.mean([p[1] for p in prediction_buffer])

                if mean_probability >= 0.5:
                    print_log("Timer still active due to sufficient average probability.")
                    prediction_buffer.append((current_time, probability))
                else:
                    print_log("Timer stopped due to low average probability.")
                    last_detection_time = 0
                    prediction_buffer.clear()

        if last_detection_time > 0 and (current_time - last_detection_time >= 15):
            mean_probability = np.mean([p[1] for p in prediction_buffer])
            if mean_probability > 0.5:
                coffee_count += 1
                print_log("Coffee count increased. Total cups brewed: " + str(coffee_count))
                update_counter_file()

                last_detection_time = time.time()
                prediction_buffer = [(last_detection_time, probability)]
                print_log("Timer restarted with current time and last event.")
            else:
                print_log("Timer stopped due to insufficient average probability at 15 seconds.")
                last_detection_time = 0
                prediction_buffer.clear()

def on_mqtt_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode("utf-8"))

        if isinstance(payload, dict) and 'apower' in payload:
            power = float(payload['apower'])
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print_log(f"Received power: {power} W")

            log_power_data(timestamp, power)

            event_buffer.append(power)
            if len(event_buffer) > 15:
                event_buffer.pop(0)

            predict_coffee()

    except json.JSONDecodeError:
        print_log("Invalid JSON message received")

initialize_log_file()
initialize_counter_file()

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_mqtt_message

print_log("Connecting to MQTT broker...")
mqtt_client.connect(MQTT_BROKER_ADDRESS, MQTT_PORT)

mqtt_client.subscribe(MQTT_TOPIC)
print_log(f"Subscribed to topic {MQTT_TOPIC}")

mqtt_client.loop_forever()
