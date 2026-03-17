import pymongo
from gpiozero import DigitalInputDevice
from datetime import datetime
import time

# --- Configuration ---
# Replace with your MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://dbAdmin:seniordes2266@cluster0.wuluk8i.mongodb.net/eecssenior_design"
GPIO_PIN = 23  # Update this to the GPIO pin you connected the signal wire to
CALIBRATION_FACTOR = 450  # Standard for many Adafruit flow sensors (check your datasheet)

# --- Database Setup ---
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client['water_monitor']
    collection = db['flow_logs']
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Database connection error: {e}")
    exit()

# --- Sensor Logic ---
pulse_count = 0

def count_pulse():
    global pulse_count
    pulse_count += 1

# Initialize the sensor pin (ensure your voltage divider is in place!)
sensor = DigitalInputDevice(GPIO_PIN, pull_up=False)
sensor.when_activated = count_pulse

print("Monitoring flow... Press Ctrl+C to stop.")

try:
    while True:
        # Reset count for the next interval
        pulse_count = 0
        time.sleep(10)  # Measure over a 10-second window
        
        # Calculation: (Pulses / Calibration Factor) = Liters per minute
        # For a 10s window, we multiply by 6 to get the minute rate
        flow_rate = (pulse_count / CALIBRATION_FACTOR)
        
        # Prepare the payload
        payload = {
            "timestamp": datetime.utcnow(),
            "pulses": pulse_count,
            "water_consumed": round(flow_rate, 3),
            "unit": "L",
            "device": "rpi_zero_2"
        }
        
        # Upload to MongoDB
        try:
            res = collection.insert_one(payload)
            print(f"Logged: {flow_rate} L/min | ID: {res.inserted_id}")
        except Exception as e:
            print(f"Failed to upload: {e}")

except KeyboardInterrupt:
    print("\nMonitoring stopped.")