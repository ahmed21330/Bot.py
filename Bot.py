import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# إعداد التوكن
TELEGRAM_BOT_TOKEN = "8146057899:AAGJ1dWtUa8gI5GxE_xaF2VZAxHii7NV9DQ"
RUNWAYML_API_KEY = "key_3211429394575bcc8c7a626aa035e0957d7d746702fc3b1a75bdbb604cc8d91cdd24e504b5a0da0a57664ba45907629817d12625155a41ebd55df1f4067cb750"

# إعداد سجل الطلبات لكل مستخدم
user_requests = {}

# إعداد الردود الافتراضية
language_options = [["العربية"], ["الإنجليزية"], ["الفرنسية"]]
video_type_options = [["شخصية ناطقة"], ["فيديو سينمائي"]]
duration_options = [["5 ثوانٍ"], ["10 ثوانٍ"], ["30 ثانية"], ["دقيقة"]]
voice_type_options = [["عميق"], ["متوسط"], ["حاد"]]

# تعيين الحالات
LANGUAGE, VIDEO_TYPE, DURATION, VOICE_TYPE, CONTENT, MEDIA = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_requests[update.message.chat_id] = {}
    reply_markup = ReplyKeyboardMarkup(language_options, one_time_keyboard=True)
    await update.message.reply_text("🎬 مرحبًا! ما هي لغة الفيديو؟", reply_markup=reply_markup)
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_requests[update.message.chat_id]["language"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(video_type_options, one_time_keyboard=True)
    await update.message.reply_text("📽️ اختر نوع الفيديو:", reply_markup=reply_markup)
    return VIDEO_TYPE

async def set_video_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_requests[update.message.chat_id]["video_type"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(duration_options, one_time_keyboard=True)
    await update.message.reply_text("⏳ اختر مدة الفيديو:", reply_markup=reply_markup)
    return DURATION

async def set_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_requests[update.message.chat_id]["duration"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(voice_type_options, one_time_keyboard=True)
    await update.message.reply_text("🔊 اختر نوع الصوت:", reply_markup=reply_markup)
    return VOICE_TYPE

async def set_voice_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_requests[update.message.chat_id]["voice_type"] = update.message.text
    await update.message.reply_text("✍️ أرسل نص الفكرة أو السيناريو الخاص بالفيديو:")
    return CONTENT

async def set_video_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_requests[update.message.chat_id]["content"] = update.message.text
    await update.message.reply_text("📷 إذا كنت تريد إضافة صور أو فيديوهات، أرسلها الآن، أو أرسل 'تخطي' للمتابعة.")
    return MEDIA

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.video:
        user_requests[update.message.chat_id]["media"] = update.message.photo[-1].file_id if update.message.photo else update.message.video.file_id
        await update.message.reply_text("✅ تم استلام الوسائط! جاري إنشاء الفيديو... يرجى الانتظار.")
    elif update.message.text.lower() == "تخطي":
        await update.message.reply_text("🎬 يتم إنشاء الفيديو... يرجى الانتظار!")

    # استدعاء RunwayML لإنشاء الفيديو
    video_path = generate_video(user_requests[update.message.chat_id])

    # إرسال الفيديو للمستخدم
    await update.message.reply_video(video=open(video_path, 'rb'))
    return ConversationHandler.END

def generate_video(user_data):
    """
    استدعاء RunwayML لإنشاء الفيديو بناءً على بيانات المستخدم.
    """
    runwayml_url = "https://api.runwayml.com/v1/generate_video"
    headers = {"Authorization": f"Bearer {RUNWAYML_API_KEY}"}
    payload = {
        "text": user_data["content"],
        "language": user_data["language"],
        "duration": user_data["duration"],
        "voice": user_data["voice_type"],
        "video_type": user_data["video_type"]
    }

    response = requests.post(runwayml_url, json=payload, headers=headers)

    if response.status_code == 200:
        video_url = response.json().get("video_url")
        video_path = "generated_video.mp4"
        with open(video_path, "wb") as file:
            file.write(requests.get(video_url).content)
        return video_path
    else:
        return "error.mp4"

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إعداد ConversationHandler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            VIDEO_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_video_type)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_duration)],
            VOICE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_voice_type)],
            CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_video_content)],
            MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO | filters.TEXT, receive_media)],
        },
        fallbacks=[],
    )

    app.add_handler(conversation_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
