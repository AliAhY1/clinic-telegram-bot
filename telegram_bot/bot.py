# bot.py

from dotenv import load_dotenv
import os
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from handlers.conversation import (
    start_booking,
    handle_name,
    handle_gender,
    handle_phone_method,
    handle_phone_input,
    handle_province,
    handle_city_input,
    handle_notes,
    handle_confirm,
    invalid_button,
    invalid_text,
    cancel,  # ← مهم جداً
)

from states import (
    STATE_NAME,
    STATE_GENDER,
    STATE_PHONE_METHOD,
    STATE_PHONE_INPUT,
    STATE_CITY_PROVINCE,
    STATE_CITY_INPUT,
    STATE_NOTES,
    STATE_CONFIRM,
)

from utils.messages import WELCOME_MESSAGE
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext


# ---------------------------------------------------------
#  🔥 1) Handler لالتقاط chat_id + username + phone + photo
# ---------------------------------------------------------
async def capture_user_info(update: Update, context: CallbackContext):

    if not update.message:
        return

    chat = update.message.chat

    chat_id = chat.id
    username = chat.username
    first_name = chat.first_name
    last_name = chat.last_name
    phone = None
    photo_url = None

    # إذا المستخدم أرسل رقم هاتفه كبطاقة Contact
    if update.message.contact:
        phone = update.message.contact.phone_number

    # محاولة جلب الصورة الشخصية
    try:
        photos = await context.bot.get_user_profile_photos(chat_id)
        if photos.total_count > 0:
            file_id = photos.photos[0][0].file_id
            file = await context.bot.get_file(file_id)
            photo_url = file.file_path
    except:
        pass

    # إرسال البيانات للـ Laravel
    try:
        requests.post(
            "https://monometrical-edward-peripherally.ngrok-free.dev/api/save-telegram-data",
            json={
                "chat_id": chat_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "photo_url": photo_url,
            },
        )
    except Exception as e:
        print("❌ Error sending Telegram data:", e)


# ---------------------------------------------------------
#  /start — رسالة الترحيب + زر حجز موعد
# ---------------------------------------------------------
async def start(update, context):
    keyboard = [["حجز موعد"]]

    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


# ---------------------------------------------------------
#  /help — مساعدة بسيطة
# ---------------------------------------------------------
async def help_cmd(update, context):
    await update.message.reply_text("للبدء بحجز موعد، اضغط على زر (حجز موعد).")


# ---------------------------------------------------------
#  إنشاء ConversationHandler
# ---------------------------------------------------------
def build_conversation_handler():

    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^حجز موعد$"), start_booking)],
        states={
            STATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            STATE_GENDER: [CallbackQueryHandler(handle_gender)],
            STATE_PHONE_METHOD: [CallbackQueryHandler(handle_phone_method)],
            STATE_PHONE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input)
            ],
            STATE_CITY_PROVINCE: [CallbackQueryHandler(handle_province)],
            STATE_CITY_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_input)
            ],
            STATE_NOTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_notes)
            ],
            STATE_CONFIRM: [CallbackQueryHandler(handle_confirm)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),  
            CallbackQueryHandler(invalid_button),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        allow_reentry=True,
    )


# ---------------------------------------------------------
#  تشغيل البوت
# ---------------------------------------------------------
def main():
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    # 🔥 يلتقط كل الرسائل ويحفظ chat_id + username + phone + photo
    app.add_handler(MessageHandler(filters.ALL, capture_user_info))

    # أوامر عامة
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # محادثة الحجز
    app.add_handler(build_conversation_handler())

    print("🤖 البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
