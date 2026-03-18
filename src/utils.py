# src/utils.py

from datetime import datetime
from pytz import timezone

def est_now():
	return datetime.now(timezone('US/Eastern'))

def utc_now():
	return datetime.now(timezone('UTC'))