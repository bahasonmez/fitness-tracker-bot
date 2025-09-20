from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from firebase_utils import get_user, create_user, update_last_active
from handlers.start import start_command, help_command

async def post_init(application: Application):
    print("Bot başlatıldı!")

async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    existing_user = get_user(telegram_id)
    if not existing_user:
        create_user(telegram_id, user.username)
    else:
        update_last_active(telegram_id)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Her komuttan önce kullanıcıyı takip et
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Middleware benzeri: Her gelen mesajda kullanıcıyı takip et
    # Bunun için MessageHandler ile track_user ekleyebiliriz, ama şimdilik komutlara özel handler içinde çağıracağız.

    print("Bot çalışıyor...")
    application.run_polling()

if __name__ == '__main__':
    main()