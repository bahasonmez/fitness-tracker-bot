from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from firebase_utils import get_user_videos, save_video_metadata, db
from utils.helpers import COMMON_EXERCISES

# --- /upload_video için ---
ASK_EXERCISE_FOR_VIDEO, ASK_NOTES_FOR_VIDEO = range(2)

def get_exercise_keyboard():
    keyboard = []
    row = []
    for i, exercise in enumerate(COMMON_EXERCISES):
        row.append(InlineKeyboardButton(exercise, callback_data=f"vid_{exercise}"))
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("➕ Yeni Hareket Ekle", callback_data="vid_new")])
    return InlineKeyboardMarkup(keyboard)

async def upload_video_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎥 Lütfen formunu gösteren bir video gönder.")
    return ASK_EXERCISE_FOR_VIDEO

async def ask_exercise_for_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text("Lütfen bir video gönder.")
        return ASK_EXERCISE_FOR_VIDEO

    file_id = update.message.video.file_id
    context.user_data['video_file_id'] = file_id

    await update.message.reply_text(
        "📌 Bu video hangi harekete ait?",
        reply_markup=get_exercise_keyboard()
    )
    return ASK_NOTES_FOR_VIDEO

async def handle_video_exercise_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "vid_new":
        await query.edit_message_text("✍️ Lütfen hareketin adını yaz:")
        return ASK_NOTES_FOR_VIDEO

    elif data.startswith("vid_"):
        exercise = data[4:]  # "vid_Squat" → "Squat"
        context.user_data['exercise'] = exercise
        await query.edit_message_text(f"✅ {exercise} seçildi.\n📝 Not eklemek ister misin?")
        return ASK_NOTES_FOR_VIDEO

    return ASK_NOTES_FOR_VIDEO

async def save_video_metadata_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id

    if 'exercise' not in context.user_data:
        raw_exercise = update.message.text.strip()
        if not raw_exercise:
            await update.message.reply_text("Lütfen hareket adı gir.")
            return ASK_NOTES_FOR_VIDEO
        exercise = raw_exercise
        context.user_data['exercise'] = exercise
    else:
        exercise = context.user_data['exercise']

    notes_text = update.message.text.strip()
    if notes_text.lower() in ['hayır', 'no', 'yok', '']:
        notes = None
    else:
        notes = notes_text

    if 'video_file_id' not in context.user_data:
        await update.message.reply_text("Önce video göndermelisin. /upload_video ile tekrar dene.")
        return ConversationHandler.END

    file_id = context.user_data['video_file_id']

    try:
        save_video_metadata(telegram_id, file_id, exercise, notes)
        await update.message.reply_text(
            f"✅ Video kaydedildi!\n"
            f"▫️ Hareket: {exercise}\n"
            f"▫️ Not: {notes or '—'}\n\n"
            f"🎬 /list_videos {exercise} ile tekrar izleyebilirsin."
        )
    except Exception as e:
        print(f"Video kaydetme hatası: {e}")
        await update.message.reply_text("❌ Video kaydedilemedi.")

    context.user_data.pop('video_file_id', None)
    context.user_data.pop('exercise', None)
    return ConversationHandler.END

async def cancel_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Video yükleme iptal edildi.")
    return ConversationHandler.END

def get_upload_video_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("upload_video", upload_video_start)],
        states={
            ASK_EXERCISE_FOR_VIDEO: [MessageHandler(filters.VIDEO, ask_exercise_for_video)],
            ASK_NOTES_FOR_VIDEO: [
                CallbackQueryHandler(handle_video_exercise_selection),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_video_metadata_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_video)],
        allow_reentry=True
    )

# --- /list_videos için ---
SELECT_EXERCISE, SELECT_DATE = range(2)

def get_video_exercise_keyboard():
    keyboard = []
    row = []
    for i, exercise in enumerate(COMMON_EXERCISES):
        row.append(InlineKeyboardButton(exercise, callback_data=f"listex_{exercise}"))
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
            print(f"[DEBUG] Eklenen satır: {row}")  # Sadece debug
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_date_keyboard(videos):
    keyboard = []
    row = []
    for i, video in enumerate(videos):
        if not isinstance(video, dict):
            print(f"[HATA] video {i} bir dict değil: {video}")
            continue

        created_at = video.get('created_at')
        if hasattr(created_at, 'strftime'):
            date_str = created_at.strftime('%d/%m/%Y')
        else:
            date_str = f"Video {i+1}"
        
        video_id = video.get('id', 'unknown')
        row.append(InlineKeyboardButton(f"📅 {date_str}", callback_data=f"showvid_{video_id}"))
        
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Geri", callback_data="back_to_exercise")])
    return InlineKeyboardMarkup(keyboard)

async def list_videos_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Hangi hareketin videolarını görmek istersin?",
        reply_markup=get_video_exercise_keyboard()
    )
    return SELECT_EXERCISE

async def show_video_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    print(f"[DEBUG] Callback verisi: '{data}'")  # Sadece debug
    if not data.startswith("listex_"):
        return SELECT_EXERCISE
    
    prefix = "listex_"
    if data.startswith(prefix):
        exercise = data[len(prefix):]

    context.user_data['selected_exercise'] = exercise  # 👈 Normalize YOK, direkt ata
    user = update.effective_user
    videos = get_user_videos(user.id, exercise)  # 👈 Orijinal isimle sorgula

    if not videos:
        await query.edit_message_text(f"❌ '{exercise}' için henüz video kaydı bulunmuyor.")
        return ConversationHandler.END

    await query.edit_message_text(
        f"📹 {exercise} için {len(videos)} video bulundu.\nHangi tarihteki videoyu izlemek istersin?",
        reply_markup=get_date_keyboard(videos)
    )
    return SELECT_DATE

async def send_selected_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_exercise":
        await query.edit_message_text(
            "🎬 Hangi hareketin videolarını görmek istersin?",
            reply_markup=get_video_exercise_keyboard()
        )
        return SELECT_EXERCISE

    if not data.startswith("showvid_"):
        return SELECT_DATE

    video_id = data[8:]  # "showvid_abc123" → "abc123"

    doc = db.collection('videos').document(video_id).get()
    if not doc.exists:
        await query.edit_message_text("❌ Video bulunamadı.")
        return ConversationHandler.END

    video_data = doc.to_dict()
    file_id = video_data.get('file_id')
    notes = video_data.get('notes', '—')
    created_at = video_data.get('created_at')
    date_str = created_at.strftime('%d/%m/%Y') if hasattr(created_at, 'strftime') else "Bilinmiyor"

    caption = f"📅 {date_str}\n📝 Not: {notes}"

    try:
        await context.bot.send_video(chat_id=query.message.chat_id, video=file_id, caption=caption)
        await query.message.reply_text("✅ Video gönderildi!")
    except Exception as e:
        print(f"Video gönderme hatası: {e}")
        await query.edit_message_text("❌ Video gönderilemedi. (Belki süresi doldu.)")

    return ConversationHandler.END

async def cancel_list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Video listeleme iptal edildi.")
    return ConversationHandler.END

def get_list_videos_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("list_videos", list_videos_start)],
        states={
            SELECT_EXERCISE: [CallbackQueryHandler(show_video_dates, pattern=r"^listex_")],
            SELECT_DATE: [CallbackQueryHandler(send_selected_video, pattern=r"^(showvid_|back_to_exercise)")],
        },
        fallbacks=[CommandHandler("cancel", cancel_list_videos)],
        allow_reentry=True
    )