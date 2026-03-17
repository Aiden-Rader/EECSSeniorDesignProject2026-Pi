# flow_metering.py

import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

import pymongo
from gpiozero import DigitalInputDevice

from src.utils import utc_now
from src.models import (build_device_insert_doc, build_device_state_doc, build_hydration_event_doc)

# --- Configuration ---
load_dotenv()  # automatically load environment variables, all must be setup in .env (FOR NOW)
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

DEVICES_COLLECTION = os.getenv("MONGO_DEVICES_COLLECTION", "devices")
DEVICE_STATE_COLLECTION = os.getenv("MONGO_DEVICES_COLLECTION", "device_state")
HYDRATION_EVENTS_COLLECTION = os.getenv("MONGO_HYDRATION_EVENT_COLLECTION", "hydration_events")

DEVICE_ID = os.getenv("DEVICE_ID", "pi-001")
DEVICE_NAME = os.getenv("DEVICE_NAME", "Main Pi")
GPIO_PIN = int(os.getenv("GPIO_PIN"))
CALIBRATION_FACTOR = float(os.getenv("CALIBRATION_FACTOR"))

POLLING_INTERVAL = 10

if not MONGO_URI:
	raise ValueError("Missing MONGO_URI in .env")

if not DB_NAME:
	raise ValueError("Missing DB_NAME in .env")

# --- Database Setup ---
try:
	client = pymongo.MongoClient(MONGO_URI)
	db = client[DB_NAME]
	devices_collection = db[DEVICES_COLLECTION]
	device_state_collection = db[DEVICE_STATE_COLLECTION]
	hydration_events_collection = db[HYDRATION_EVENTS_COLLECTION]
	print("Successfully connected to MongoDB.")
except Exception as e:
	print(f"Database connection error: {e}")
	raise SystemExit(1)

def get_or_create_device():
	"""
	Gets a device document from the database, or creates a new one if it doesn't exist.
	If the device exists, it updates the last seen at and status fields of the document.
	The status is set to 'online' if the device has an ownerUid, and 'unlinked' otherwise.
	Returns the device document.
	"""
	now = utc_now()

	existing_device = devices_collection.find_one({"__id": DEVICE_ID})

	if not existing_device:
		new_device = build_device_insert_doc(
			device_id=DEVICE_ID,
			owner_uid=None,
			device_name=DEVICE_NAME,
			calibration_factor=CALIBRATION_FACTOR
		)
		devices_collection.insert_one(new_device)
		return new_device

	owner_uid = existing_device.get("ownerUid")
	linked_status = "online" if owner_uid else "unlinked"

	devices_collection.update_one(
		{"__id": DEVICE_ID},
		{
			"$set": {
				"lastSeenAt": now,
				"status": linked_status,
				"isActive": True,
				"deviceName": DEVICE_NAME,
				"calibrationFactor": CALIBRATION_FACTOR
			}
		}
	)

	return devices_collection.find_one({"__id": DEVICE_ID})


def update_device_state(owner_uid, pulse_count, flow_rate_ml_per_sec, sensor_connected):
	"""Updates the device state document in the database.

	Args:
		owner_uid (str): The ownerUid of the device.
		pulse_count (int): The pulse count of the device.
		flow_rate_ml_per_sec (float): The flow rate of the device in ml/s.
		sensor_connected (bool): Whether the sensor is connected.
	"""
	payload = build_device_state_doc(
		device_id=DEVICE_ID,
		owner_uid=owner_uid,
		pulse_count=pulse_count,
		flow_rate_ml_per_sec=flow_rate_ml_per_sec,
		sensor_connected=sensor_connected
	)

	device_state_collection.update_one(
		{"deviceId": DEVICE_ID},
		{"$set": payload},
		upsert=True
	)


def insert_hydration_event(owner_uid, pulse_count, volume_ml, session_started_at, session_ended_at, duration_seconds):
	"""
	Insert a new hydration event into the database.

	Args:
		owner_uid (str): The ownerUid of the device.
		pulse_count (int): The pulse count of the device.
		volume_ml (float): The volume of liquid in ml consumed during the session.
		session_started_at (datetime): The time at which the hydration session started.
		session_ended_at (datetime): The time at which the hydration session ended.
		duration_seconds (int): The duration of the hydration session in seconds.

	Returns:
		pymongo.InsertOneResult: The result of the insert operation.
	"""
	payload = build_hydration_event_doc(
		device_id=DEVICE_ID,
		owner_uid=owner_uid,
		pulse_count=pulse_count,
		volume_ml=volume_ml,
		session_started_at=session_started_at,
		session_ended_at=session_ended_at,
		duration_seconds=duration_seconds
	)

	return hydration_events_collection.insert_one(payload)

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
	device = get_or_create_device()
	print(f"Device ready: {DEVICE_ID}")

	while True:
		session_started_at = utc_now()

		# Reset count for the next interval
		pulse_count = 0
		time.sleep(POLLING_INTERVAL)  # Measure over a 10-second window

		session_ended_at = utc_now()
		duration_seconds = POLLING_INTERVAL

		 # refresh device in case ownerUid gets linked later by frontend/backend
		device = get_or_create_device()
		owner_uid = device.get("ownerUid")

		# pulses / calibration factor = liters during interval
		liters = pulse_count / CALIBRATION_FACTOR
		volume_ml = liters * 1000
		flow_rate_ml_per_sec = volume_ml / duration_seconds if duration_seconds > 0 else 0

		# update latest device state
		try:
			update_device_state(
				owner_uid=owner_uid,
				pulse_count=pulse_count,
				flow_rate_ml_per_sec=flow_rate_ml_per_sec,
				sensor_connected=True
			)
		except Exception as e:
			print(f"Failed to update device state: {e}")

		# insert event only when real flow happened
		if pulse_count > 0:
			try:
				res = insert_hydration_event(
					owner_uid=owner_uid,
					pulse_count=pulse_count,
					volume_ml=volume_ml,
					session_started_at=session_started_at,
					session_ended_at=session_ended_at,
					duration_seconds=duration_seconds
				)
				print(
					f"Logged hydration event | pulses={pulse_count} | "
					f"volume_ml={volume_ml:.2f} | "
					f"flow_ml_per_sec={flow_rate_ml_per_sec:.2f} | "
					f"id={res.inserted_id}"
				)
			except Exception as e:
				print(f"Failed to insert hydration event: {e}")
		else:
			print("No flow detected this interval. Updated device_state only.")

except KeyboardInterrupt:
	print("\nMonitoring stopped.")