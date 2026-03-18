# telegram_bot/handlers/conversation.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from telegram_bot.states import (
    STATE_NAME,
    STATE_GENDER,
    STATE_PHONE_METHOD,
    STATE_PHONE_INPUT,
    STATE_CITY_PROVINCE,
    STATE_CITY_INPUT,
    STATE_NOTES,
    STATE_CONFIRM,
)

from telegram_bot.utils.messages import *
from telegram_bot.utils.validators import validate_name, validate_phone, validate_city_input
from telegram_bot.utils.api import create_booking, check_existing_booking, get_patient_by_chat_id
from telegram_bot.utils.photos import get_user_photo


# ---------------------------------------------------------
#  حماية الـ Flow
# ---------------------------------------------------------

async def invalid_button(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "هذه الرسالة لم تعد صالحة للاستخدام.\nيرجى المتابعة من الرسالة الأخيرة."
    )


async def invalid_text(update, context):
    await update.message.reply_text(
        "الرجاء الالتزام بالخطوة الحالية.\nيرجى متابعة الإجابات حسب التعليمات."
    )


# ---------------------------------------------------------
#  /start → زر "حجز موعد"
# ---------------------------------------------------------

async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["in_flow"] = False
    context.user_data["in_flow"] = True

    await update.message.reply_text(ASK_NAME, reply_markup=ReplyKeyboardRemove())
    return STATE_NAME


# ---------------------------------------------------------
#  /cancel → إلغاء العملية
# ---------------------------------------------------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["in_flow"] = False
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END


# ---------------------------------------------------------
#  إدخال الاسم
# ---------------------------------------------------------

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()

    if not validate_name(name):
        await update.message.reply_text("يرجى إدخال اسم ثلاثي صحيح.")
        return STATE_NAME

    context.user_data["name"] = name

    keyboard = [
        [
            InlineKeyboardButton("ذكر", callback_data="male"),
            InlineKeyboardButton("أنثى", callback_data="female"),
        ]
    ]

    await update.message.reply_text(
        ASK_GENDER, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_GENDER


# ---------------------------------------------------------
#  اختيار الجنس
# ---------------------------------------------------------

async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    gender = query.data
    context.user_data["gender"] = gender

    keyboard = [
        [
            InlineKeyboardButton(
                "استخدام الرقم الحالي من تلغرام", callback_data="use_telegram"
            )
        ],
        [InlineKeyboardButton("إدخال رقم آخر", callback_data="manual_phone")],
    ]

    await query.edit_message_text(
        ASK_PHONE_METHOD, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_PHONE_METHOD


# ---------------------------------------------------------
#  اختيار طريقة إدخال الرقم
# ---------------------------------------------------------

async def handle_phone_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    method = query.data

    if method == "use_telegram":

        phone = context.user_data.get("phone")

        if not phone:
            patient = get_patient_by_chat_id(update.effective_user.id)
            if patient and patient.get("phone"):
                phone = patient["phone"]

        if not phone:
            await query.edit_message_text(
                "لا يمكن جلب رقم الهاتف من تلغرام.\nيرجى إدخاله يدويًا."
            )
            return STATE_PHONE_INPUT

        check = check_existing_booking(phone)
        if check.get("blocked"):
            msg = "لديك حجز سابق لم يتم الانتهاء منه.\n"

            if check["status"] == "pending":
                msg += "🔸 حجزك الحالي قيد الانتظار.\n"
            elif check["status"] == "approved":
                msg += "🔸 لديك موعد محدد لم يحن وقته بعد.\n"

            msg += "\nلا يمكنك إرسال طلب جديد قبل انتهاء الحجز السابق."

            await query.edit_message_text(msg)
            context.user_data["in_flow"] = False
            return ConversationHandler.END

        context.user_data["phone"] = phone

        return await ask_province(query, context)

    else:
        await query.edit_message_text(ASK_PHONE_INPUT)
        return STATE_PHONE_INPUT


# ---------------------------------------------------------
#  إدخال رقم الهاتف يدويًا
# ---------------------------------------------------------

async def handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()

    if not validate_phone(phone):
        await update.message.reply_text("رقم الهاتف غير صالح. يرجى إدخال رقم صحيح.")
        return STATE_PHONE_INPUT

    check = check_existing_booking(phone)

    if check.get("blocked"):
        msg = "لديك حجز سابق لم يتم الانتهاء منه.\n"

        if check["status"] == "pending":
            msg += "🔸 حجزك الحالي قيد الانتظار.\n"
        elif check["status"] == "approved":
            msg += "🔸 لديك موعد محدد لم يحن وقته بعد.\n"

        msg += "\nلا يمكنك إرسال طلب جديد قبل انتهاء الحجز السابق."

        await update.message.reply_text(msg)
        context.user_data["in_flow"] = False
        return ConversationHandler.END

    context.user_data["phone"] = phone

    return await ask_province(update, context)


# ---------------------------------------------------------
#  إرسال قائمة المحافظات
# ---------------------------------------------------------

async def ask_province(update_or_query, context):
    provinces = [
        ["دمشق", "ريف دمشق", "حمص"],
        ["حماة", "اللاذقية", "طرطوس"],
        ["حلب", "إدلب", "الحسكة"],
        ["الرقة", "دير الزور", "السويداء"],
        ["درعا", "القنيطرة"],
    ]

    keyboard = [
        [InlineKeyboardButton(p, callback_data=f"prov_{p}") for p in row]
        for row in provinces
    ]

    if hasattr(update_or_query, "message"):
        await update_or_query.message.reply_text(
            ASK_CITY_PROVINCE, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update_or_query.edit_message_text(
            ASK_CITY_PROVINCE, reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return STATE_CITY_PROVINCE


# ---------------------------------------------------------
#  اختيار المحافظة
# ---------------------------------------------------------

async def handle_province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    province = query.data.replace("prov_", "")
    context.user_data["province"] = province

    await query.edit_message_text(ASK_CITY_INPUT)
    return STATE_CITY_INPUT


# ---------------------------------------------------------
#  إدخال المدينة/المنطقة
# ---------------------------------------------------------

async def handle_city_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()

    if not validate_city_input(city):
        await update.message.reply_text("يرجى إدخال اسم مدينة أو منطقة صالح.")
        return STATE_CITY_INPUT

    context.user_data["city"] = city

    await update.message.reply_text(ASK_NOTES)
    return STATE_NOTES


# ---------------------------------------------------------
#  إدخال الملاحظات
# ---------------------------------------------------------

async def handle_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = update.message.text.strip()
    context.user_data["notes"] = "" if notes == "لا" else notes

    photo_url = await get_user_photo(update.get_bot(), update.effective_user.id)
    context.user_data["photo_url"] = photo_url

    summary = (
        f"{CONFIRM_HEADER}"
        f"الاسم: {context.user_data['name']}\n"
        f"الجنس: {'ذكر' if context.user_data['gender']=='male' else 'أنثى'}\n"
        f"رقم الهاتف: {context.user_data['phone']}\n"
        f"المحافظة: {context.user_data['province']}\n"
        f"المدينة/المنطقة: {context.user_data['city']}\n"
        f"الملاحظات: {context.user_data['notes'] or 'لا يوجد'}\n"
    )

    keyboard = [
        [InlineKeyboardButton("تأكيد الإرسال", callback_data="confirm")],
        [InlineKeyboardButton("إلغاء", callback_data="cancel")],
    ]

    await update.message.reply_text(
        summary, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_CONFIRM


# ---------------------------------------------------------
#  تأكيد أو إلغاء
# ---------------------------------------------------------

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text(CANCEL_MESSAGE)
        context.user_data["in_flow"] = False
        return ConversationHandler.END

    data = {
        "name": context.user_data["name"],
        "gender": context.user_data["gender"],
        "phone": context.user_data["phone"],
        "province": context.user_data["province"],
        "city": context.user_data["city"],
        "notes": context.user_data["notes"],
        "telegram_username": update.effective_user.username,
    }

    success = create_booking(data)

    if success:
        await query.edit_message_text(SUCCESS_MESSAGE)
    else:
        await query.edit_message_text("حدث خطأ أثناء إرسال الطلب. يرجى المحاولة لاحقًا.")

    context.user_data["in_flow"] = False
    return ConversationHandler.END
