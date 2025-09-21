from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from handlers.start import start_command, help_command
from handlers.workout import get_log_workout_handler
from handlers.video import get_upload_video_handler, get_list_videos_handler
from handlers.measurement import get_log_measurement_handler
from handlers.stats import stats_command
import os

async def post_init(application: Application):
    print("🚀 Fitness Takip Botu Başlatıldı!")

async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    from firebase_utils import get_user, update_last_active
    existing_user = get_user(telegram_id)
    if existing_user:
        update_last_active(telegram_id)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(get_log_workout_handler())
    application.add_handler(get_upload_video_handler())
    application.add_handler(get_log_measurement_handler())
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(get_list_videos_handler())

    print("✅ Bot webhook modda başlatılıyor...")

    # 👇 WEBHOOK MODU — Cloud Run için gerekli
    PORT = int(os.environ.get('PORT', '8080'))
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

    if WEBHOOK_URL:
        # Webhook'u set et
        application.bot.set_webhook(url=WEBHOOK_URL)
        # Webhook modda başlat
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=WEBHOOK_URL
        )
    else:
        # Geliştirme modu — polling
        application.run_polling()

if __name__ == '__main__':
    main()