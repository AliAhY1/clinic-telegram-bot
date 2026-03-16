# states.py

from telegram.ext import ConversationHandler

(
    STATE_NAME,
    STATE_GENDER,
    STATE_PHONE_METHOD,
    STATE_PHONE_INPUT,
    STATE_CITY_PROVINCE,
    STATE_CITY_INPUT,
    STATE_NOTES,
    STATE_CONFIRM,
) = range(8)
