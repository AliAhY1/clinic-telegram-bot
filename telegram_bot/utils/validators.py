# utils/validators.py

import re


def validate_name(name: str) -> bool:
    parts = name.strip().split()
    return len(parts) == 3 and all(p.isalpha() for p in parts)


def validate_phone(phone: str) -> bool:
    phone = phone.strip()
    return phone.isdigit() and 8 <= len(phone) <= 15


def clean_notes(notes: str) -> str:
    if notes.strip().lower() == "لا":
        return ""
    return notes.strip()


def validate_city_input(city: str) -> bool:
    return city.replace(" ", "").isalpha()


def is_doctor(user_id: int) -> bool:
    # هون رح نحط chat_id الحقيقي للدكتور بعد ما تجيبه من /id
    DOCTOR_IDS = [
        # مثال:
        # 123456789,
    ]
    return user_id in DOCTOR_IDS
