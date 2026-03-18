import os
import asyncio
import requests
from dotenv import load_dotenv
from aiohttp import web

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# تحميل env
load_dotenv()

# استيراد ملفات البوت
from telegram_bot.handlers.conversation import (
    start_booking, handle_name, handle_gender, handle_phone_method,
    handle_phone_input, handle_province, handle_city_input,
    handle_notes, handle_confirm, invalid_button, invalid_text, cancel
)

from telegram_bot.states import (
    STATE_NAME, STATE_GENDER, STATE_PHONE_METHOD, STATE_PHONE_INPUT,
    STATE_CITY_PROVINCE, STATE_CITY_INPUT, STATE_NOTES, STATE_CONFIRM
)

from telegram_bot.utils.messages import WELCOME_MESSAGE


# ---------------------------------------------------------
#  /start
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["حجز موعد"]]
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


# ---------------------------------------------------------
#  /help
# ---------------------------------------------------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("للبدء بحجز موعد، اضغط على زر (حجز موعد).")


# ---------------------------------------------------------
#  تشغيل البوت + Webhook Server
# ---------------------------------------------------------
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.environ.get("PORT", 8080))

    # إنشاء التطبيق
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^حجز موعد$"), start_booking)],
        states={
            STATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            STATE_GENDER: [CallbackQueryHandler(handle_gender)],
            STATE_PHONE_METHOD: [CallbackQueryHandler(handle_phone_method)],
            STATE_PHONE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input)],
            STATE_CITY_PROVINCE: [CallbackQueryHandler(handle_province)],
            STATE_CITY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_input)],
            STATE_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_notes)],
            STATE_CONFIRM: [CallbackQueryHandler(handle_confirm)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(invalid_button),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    # -----------------------------
    #  aiohttp Webhook Server
    # -----------------------------
    async def handle(request):
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response(text="OK")

    aio_app = web.Application()
    aio_app.router.add_post(f"/{TOKEN}", handle)

    # إعداد الويب هوك
    await app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

    print("🤖 Webhook server is running on Railway...")

    # تشغيل السيرفر
    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # إبقاء البوت شغال
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
