from telegram import Update
from telegram.ext import ContextTypes
from firebase_utils import get_user, create_user, update_last_active

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    existing_user = get_user(telegram_id)
    
    if not existing_user:
        create_user(telegram_id, user.username)
        await update.message.reply_text(
            f"👋 Merhaba {user.username}! Fitness takip botuna hoş geldin.\n"
            "Şu komutlarla başlayabilirsin:\n"
            "/log_workout - Antrenman kaydı gir\n"
            "/upload_video - Video yükle\n"
            "/log_measurement - Vücut ölçüsü gir\n"
            "/stats - İstatistiklerini gör"
        )
    else:
        update_last_active(telegram_id)
        await update.message.reply_text(
            f"🌟 Tekrar hoş geldin {user.username}!\nDevam etmek için /help yazabilirsin."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_last_active(user.id)
    
    help_text = """
📋 **Fitness Takip Botu Komutları**

🏋️‍♂️ *Antrenman*
/log_workout - Set, tekrar, kg gir
/upload_video - Hareket videosu yükle

📏 *Vücut Ölçüleri*
/log_measurement - Aylık ölçümlerini kaydet

📊 *Raporlar*
/stats - Genel ilerleme grafiği
/stats <hareket> - Belirli hareketin grafiği

💾 *Veri Yönetimi*
/export_data - Verilerini dışa aktar (CSV)

❓ /help - Bu menü
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")