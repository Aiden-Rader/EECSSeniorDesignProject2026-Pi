# src/models.py

from .utils import utc_now, est_now

# Device Model
def build_device_insert_doc(device_id, owner_uid, device_name, calibration_factor, linked_status="unlinked"):
	now = est_now()
	return {
		"_id": device_id,
		"ownerUid": owner_uid if owner_uid else None,
		"deviceName": device_name,
		"calibrationFactor": calibration_factor,
		"createdAt": now,
		"lastSeenAt": now,
		"status": linked_status,
		"isActive": True
	}

# Device State Model
def build_device_state_doc(device_id, owner_uid, pulse_count, flow_rate_ml_per_sec, sensor_connected):
	return {
		"deviceId": device_id,
		"ownerUid": owner_uid,
		"updatedAt": est_now(),
		"data": {
			"currentPulseCount": pulse_count,
			"currentFlowRateMlPerSec": flow_rate_ml_per_sec,
			"sensorConnected": sensor_connected,
			"hasWater": True  # TODO: For now assume the device has water until we get other sensor data
		}
	}

# Hydration Event Model
def build_hydration_event_doc(device_id, owner_uid, pulse_count, volume_ml, session_started_at, session_ended_at, duration_seconds):
	return {
		"deviceId": device_id,
		"ownerUid": owner_uid,
		"createdAt": est_now(),
		"data": {
			"pulseCount": pulse_count,
			"volumeMl": volume_ml,
			"sessionStartedAt": session_started_at,
			"sessionEndedAt": session_ended_at,
			"durationSeconds": duration_seconds
		}
	}
