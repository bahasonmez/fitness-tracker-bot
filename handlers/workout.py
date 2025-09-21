from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from firebase_utils import log_workout, get_user_workouts
from utils.helpers import COMMON_EXERCISES
import logging

# Adımlar
ASK_EXERCISE, ASK_SETS, ASK_REPS, ASK_WEIGHT, ASK_NOTES = range(5)

# PR kontrolü
def check_pr(user_id, exercise_name, new_weight):
    workouts = get_user_workouts(user_id, exercise_name)
    if not workouts:
        return True
    max_weight = max(w.get('weight_kg', 0) for w in workouts)
    return new_weight > max_weight

# Buton klavyesi oluştur
def get_exercise_keyboard():
    keyboard = []
    row = []
    for i, exercise in enumerate(COMMON_EXERCISES):
        row.append(InlineKeyboardButton(exercise, callback_data=f"ex_{exercise}"))
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("➕ Yeni Hareket Ekle", callback_data="ex_new")])
    return InlineKeyboardMarkup(keyboard)

# /log_workout — Buton göster
async def log_workout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏋️ Hangi hareketi yaptın?",
        reply_markup=get_exercise_keyboard()
    )
    return ASK_EXERCISE

# Butona tıklanınca
async def handle_exercise_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "ex_new":
        await query.edit_message_text("✍️ Lütfen hareketin adını yaz:")
        return ASK_EXERCISE

    elif data.startswith("ex_"):
        exercise = data[3:]  # "ex_Squat" → "Squat" — ✅ ZATEN ORİJİNAL İSİM
        context.user_data['exercise'] = exercise  # 👈 Normalize yok, direkt ata
        await query.edit_message_text(f"✅ {exercise} seçildi.\n🔢 Kaç set yaptın?")
        return ASK_SETS

    return ASK_EXERCISE


# Yeni hareket metin girişi
async def ask_sets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exercise = update.message.text.strip()
    if not exercise:
        await update.message.reply_text("Lütfen geçerli bir hareket adı gir.")
        return ASK_EXERCISE
    
    # 👇 Normalize ETME, direkt kaydet
    context.user_data['exercise'] = exercise  # ✅ Orijinal ismi kaydet
    
    await update.message.reply_text(f"🔢 {exercise} için kaç set yaptın?")
    return ASK_SETS

# Set → Tekrar
async def ask_reps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sets = int(update.message.text)
        if sets <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text("Lütfen pozitif bir sayı gir. (Örn: 3, 5)")
        return ASK_SETS

    context.user_data['sets'] = sets
    await update.message.reply_text("🔁 Kaç tekrar yaptın? (Her set için)")
    return ASK_REPS

# Tekrar → Ağırlık
async def ask_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        reps = int(update.message.text)
        if reps <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text("Lütfen pozitif bir tekrar sayısı gir. (Örn: 8, 12)")
        return ASK_REPS

    context.user_data['reps'] = reps
    await update.message.reply_text("🏋️‍♂️ Kaç kg kaldırdın?")
    return ASK_WEIGHT

# Ağırlık → Not
async def ask_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        if weight < 0: raise ValueError
    except ValueError:
        await update.message.reply_text("Lütfen geçerli bir ağırlık gir. (Örn: 40.5, 60)")
        return ASK_WEIGHT

    context.user_data['weight'] = weight
    await update.message.reply_text("📝 Not eklemek ister misin? (İstemiyorsan 'hayır' yazabilirsin.)")
    return ASK_NOTES

# Kaydet
async def save_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id

    exercise = context.user_data['exercise']
    sets = context.user_data['sets']
    reps = context.user_data['reps']
    weight = context.user_data['weight']
    notes = update.message.text.strip()
    if notes.lower() in ['hayır', 'no', 'yok', '']:
        notes = None

    try:
        log_workout(telegram_id, exercise, sets, reps, weight, notes=notes)
        is_pr = check_pr(telegram_id, exercise, weight)
        pr_msg = " 🎉 YENİ PR!" if is_pr else ""

        await update.message.reply_text(
            f"✅ Kaydedildi!\n"
            f"▫️ Hareket: {exercise}\n"
            f"▫️ Set: {sets}\n"
            f"▫️ Tekrar: {reps}\n"
            f"▫️ Ağırlık: {weight} kg{pr_msg}\n"
            f"▫️ Not: {notes or '—'}"
        )
    except Exception as e:
        logging.error(f"Workout save error: {e}")
        await update.message.reply_text("❌ Kayıt sırasında hata oluştu.")

    return ConversationHandler.END

# İptal
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Antrenman kaydı iptal edildi.")
    return ConversationHandler.END

# Ana handler
def get_log_workout_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("log_workout", log_workout_start)],
        states={
            ASK_EXERCISE: [
                CallbackQueryHandler(handle_exercise_selection),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sets)
            ],
            ASK_SETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_reps)],
            ASK_REPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_weight)],
            ASK_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_notes)],
            ASK_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_workout)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
        # 👆 per_message, per_user vs. EKLEME! UYARI GELSE DE ÇALIŞIR.
    )