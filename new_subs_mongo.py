import collections
import numpy as np
import pandas as pd
import joblib
import paho.mqtt.client as mqtt
import json
from pymongo import MongoClient

# Load your trained model and label encoder
model = joblib.load('trained_model.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# Define the ranges for each parameter
ph_range = (8.5, 9.5)
temperature_range = (25.5, 30)
tds_range = (250, 360)
turbidity_range = (5, 100)

# MQTT broker details
mqtt_broker = "192.168.0.113"
mqtt_port = 1883
mqtt_topic = "sensors/data"

# MongoDB details
mongodb_host = "localhost"
mongodb_port = 27017
mongodb_database = "algae"
mongodb_collection = "water_body"

# Create a MongoDB client and connect to the database
mongodb_client = MongoClient(mongodb_host, mongodb_port)
database = mongodb_client[mongodb_database]
collection = database[mongodb_collection]

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(mqtt_topic)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)

    # Print all values
    print("!-----------------------------------------------------------------------------------------------------")
    print(" The payload is : ")
    print(" Timestamp:", payload["timestamp"])
    print(" Temperature:", payload["temperature"])
    print(" TDS:", payload["tds"])
    print(" pH:", payload["ph"])
    print(" Turbidity:", payload["turbidity"])
    print("-----------------------------------------------------------------------------------------------------")

    # Store real-time sensor data in variables
    real_time_ph = payload["ph"]
    real_time_temperature = payload["temperature"]
    real_time_tds = payload["tds"]
    real_time_turbidity = payload["turbidity"]

    # Check if all parameters are within the specified ranges
    if (ph_range[0] <= real_time_ph <= ph_range[1]) and \
       (temperature_range[0] <= real_time_temperature <= temperature_range[1]) and \
       (tds_range[0] <= real_time_tds <= tds_range[1]) and \
       (turbidity_range[0] <= real_time_turbidity <= turbidity_range[1]):

        # Insert data into MongoDB collection
        collection.insert_one(payload)

        # Prepare the real-time data in the same format as your training data
        real_time_data = np.array([[real_time_ph, real_time_temperature, real_time_tds, real_time_turbidity]])

        # Make predictions using the loaded model
        predicted_numerical = model.predict(real_time_data)

        # Convert the predicted numeric label to integer
        predicted_numerical = np.round(predicted_numerical).astype(int)

        # Convert the predicted numeric label back to the original categorical label
        predicted_category = label_encoder.inverse_transform(predicted_numerical)

        print(f"Predicted category for real-time data: {predicted_category[0]}")
        print("Algae is present")
    else:
        print("Warning: Real-time data is out of specified parameter ranges.")

# Create an MQTT client instance
client = mqtt.Client()

# Configure MQTT callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(mqtt_broker, mqtt_port, 60)

# Start the MQTT client loop in a separate thread
import threading
mqtt_thread = threading.Thread(target=client.loop_forever)
mqtt_thread.start()