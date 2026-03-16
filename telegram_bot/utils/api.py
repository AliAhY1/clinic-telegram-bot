# utils/api.py

import requests
import os

API_BASE = os.getenv("API_BASE")


def create_booking(data: dict):
    url = f"{API_BASE}/api/bookings"
    try:
        res = requests.post(url, json=data, timeout=10)
        return res.status_code == 201
    except:
        return False


def check_existing_booking(phone: str):
    url = f"{API_BASE}/api/bot/check-booking?phone={phone}"

    try:
        res = requests.get(url, timeout=10)
        return res.json()
    except:
        return {"blocked": False}


def get_patient_by_chat_id(chat_id):
    try:
        response = requests.get(f"{API_URL}/patients/by-chat/{chat_id}")
        if response.status_code == 200:
            return response.json()
    except:
        return None


