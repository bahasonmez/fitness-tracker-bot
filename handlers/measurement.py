from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler

# Adımlar
ASK_WEIGHT, ASK_WAIST, ASK_CHEST, ASK_ARM, ASK_HIP = range(5)

# Firebase'e kaydetme fonksiyonu (firebase_utils.py'den)
from firebase_utils import log_measurement

# Başlangıç
async def log_measurement_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚖️ Bugün kaç kg tartıldın? (Örn: 75.5)")
    return ASK_WEIGHT

# Kilo → Bel
async def ask_waist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        if weight <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Lütfen geçerli bir kilo gir. (Örn: 72.5)")
        return ASK_WEIGHT

    context.user_data['weight'] = weight
    await update.message.reply_text("📏 Bel çevren kaç cm? (Örn: 85)")
    return ASK_WAIST

# Bel → Göğüs
async def ask_chest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        waist = float(update.message.text)
        if waist <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Lütfen geçerli bir bel ölçüsü gir. (Örn: 82.5)")
        return ASK_WAIST

    context.user_data['waist'] = waist
    await update.message.reply_text("👕 Göğüs çevren kaç cm?")
    return ASK_CHEST

# Göğüs → Kol
async def ask_arm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chest = float(update.message.text)
        if chest <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Lütfen geçerli bir göğüs ölçüsü gir.")
        return ASK_CHEST

    context.user_data['chest'] = chest
    await update.message.reply_text("💪 Kol çevren kaç cm? (Biceps)")
    return ASK_ARM

# Kol → Kalça
async def ask_hip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        arm = float(update.message.text)
        if arm <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Lütfen geçerli bir kol ölçüsü gir.")
        return ASK_ARM

    context.user_data['arm'] = arm
    await update.message.reply_text("👖 Kalça çevren kaç cm?")
    return ASK_HIP

# Kalça → KAYDET
async def save_measurements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hip = float(update.message.text)
        if hip <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Lütfen geçerli bir kalça ölçüsü gir.")
        return ASK_HIP

    context.user_data['hip'] = hip

    user = update.effective_user
    telegram_id = user.id

    measurements = {
        'weight_kg': context.user_data['weight'],
        'waist_cm': context.user_data['waist'],
        'chest_cm': context.user_data['chest'],
        'arm_cm': context.user_data['arm'],
        'hip_cm': hip
    }

    try:
        log_measurement(telegram_id, measurements)
        await update.message.reply_text(
            f"✅ Vücut ölçümlerin kaydedildi!\n\n"
            f"▫️ Kilo: {measurements['weight_kg']} kg\n"
            f"▫️ Bel: {measurements['waist_cm']} cm\n"
            f"▫️ Göğüs: {measurements['chest_cm']} cm\n"
            f"▫️ Kol: {measurements['arm_cm']} cm\n"
            f"▫️ Kalça: {measurements['hip_cm']} cm\n\n"
            f"📊 İlerlemeni görmek için /stats komutunu kullanabilirsin."
        )
    except Exception as e:
        print(f"Measurement save error: {e}")
        await update.message.reply_text("❌ Kayıt sırasında hata oluştu.")

    # Temizle
    for key in ['weight', 'waist', 'chest', 'arm', 'hip']:
        context.user_data.pop(key, None)

    return ConversationHandler.END

# İptal
async def cancel_measurement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Ölçüm kaydı iptal edildi.")
    return ConversationHandler.END

# 👇👇👇 BU KISIM ÖNEMLİ — HANDLER'I DIŞARI AKTARIYORUZ
def get_log_measurement_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("log_measurement", log_measurement_start)],
        states={
            ASK_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_waist)],
            ASK_WAIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_chest)],
            ASK_CHEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_arm)],
            ASK_ARM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_hip)],
            ASK_HIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_measurements)],
        },
        fallbacks=[CommandHandler("cancel", cancel_measurement)],
        allow_reentry=True
    )