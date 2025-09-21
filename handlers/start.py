from telegram import Update
from telegram.ext import ContextTypes
from firebase_utils import get_user, create_user, update_last_active

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    existing_user = get_user(telegram_id)
    
    display_name = user.username or "Kullanıcı"
    
    if not existing_user:
        create_user(telegram_id, user.username)
        await update.message.reply_text(
            f"👋 Merhaba {display_name}! Fitness takip botuna hoş geldin.\n"
            "Şu komutlarla başlayabilirsin:\n"
            "/log_workout - Antrenman kaydı gir\n"
            "/upload_video - Video yükle\n"
            "/log_measurement - Vücut ölçüsü gir\n"
            "/stats - İstatistiklerini gör"
        )
    else:
        update_last_active(telegram_id)
        await update.message.reply_text(
            f"🌟 Tekrar hoş geldin {display_name}!\nDevam etmek için /help yazabilirsin."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_last_active(user.id)
    
    help_text = """
📋 *Fitness Takip Botu Yardım Menüsü*

Merhaba! İşte kullanabileceğin tüm komutlar:

🏋️‍♂️ *ANTRENMAN KAYDI*
/log_workout — Set, tekrar ve kaldırdığın ağırlığı kaydet.

🎥 *VIDEO YÜKLEME & İZLEME*
/upload_video — Hareket formunu kaydetmek için video yükle.
/list_videos — Kayıtlı videolarını listele ve izle.

📏 *VÜCUT ÖLÇÜMLERİ*
/log_measurement — Aylık olarak kilo, bel, göğüs, kol ve kalça ölçülerini gir.

📊 *İSTATİSTİKLER*
/stats — Genel ilerleme grafiklerini gör.
/stats <hareket> — Belirli bir hareketin ağırlık gelişim grafiğini göster. (Örn: /stats Squat)

💡 *İPUCU:* Tüm verilerin saklanır. İlerlemenizi grafikler ve videolarla takip edebilirsiniz!

❓ Her zaman bu menüye /help yazarak ulaşabilirsiniz.
"""
    await update.message.reply_text(help_text)
