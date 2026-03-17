import os
import time
from datetime import datetime

import pymongo
from gpiozero import DigitalInputDevice

# --- Configuration ---
MONGO_URI = "mongodb+srv://dbAdmin:seniordes2266@cluster0.wuluk8i.mongodb.net/eecssenior_design"
DB_NAME = "eecssenior_design"
COLLECTION = "telemetry"

GPIO_PIN = 23
CALIBRATION_FACTOR = 450  # Calibration factor for the flow sensor (standard for adafruit flow sensor)

# --- Database Setup ---
try:
	client = pymongo.MongoClient(MONGO_URI)
	db = client[DB_NAME]
	collection = db['telemetry']
	print("Successfully connected to MongoDB.")
except Exception as e:
	print(f"Database connection error: {e}")
	exit()

# --- Sensor Logic ---
pulse_count = 0

def count_pulse():
	global pulse_count
	pulse_count += 1

# Initialize the sensor pin
sensor = DigitalInputDevice(GPIO_PIN, pull_up=False)
sensor.when_activated = count_pulse

print("Monitoring flow... Press Ctrl+C to stop.")

try:
	while True:
		# Reset count for the next interval
		pulse_count = 0
		time.sleep(10)  # Measure over a 10-second window

		# Calculation: (Pulses / Calibration Factor) = Liters per interval
		flow_rate = (pulse_count / CALIBRATION_FACTOR)

		# Prepare the payload for MongoDB (match telemetry schema)
		payload = {

		}

		# Upload to MongoDB
		try:
			res = collection.insert_one(payload)
			print(f"Logged: {flow_rate} L/min | ID: {res.inserted_id}")
		except Exception as e:
			print(f"Failed to upload: {e}")

except KeyboardInterrupt:
	print("\nMonitoring stopped.")