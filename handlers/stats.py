from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from firebase_utils import get_user_workouts, get_user_measurements
from utils.plotter import plot_weight_progress, plot_body_measurements
import os

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id

    exercise_filter = None
    if context.args:
        exercise_filter = " ".join(context.args)

    if exercise_filter:
        workouts = get_user_workouts(telegram_id, exercise_filter)
        if not workouts:
            await update.message.reply_text(f"❌ '{exercise_filter}' için henüz kayıt bulunmuyor.")
            return

        graph_file = plot_weight_progress(workouts, exercise_filter)
        if graph_file and os.path.exists(graph_file):
            await update.message.reply_photo(photo=open(graph_file, 'rb'), caption=f"📈 {exercise_filter.title()} Ağırlık Gelişimi")
            os.remove(graph_file)
        else:
            await update.message.reply_text("Grafik oluşturulamadı.")
        return

    # Vücut ölçümleri
    measurements = get_user_measurements(telegram_id)
    if not measurements:
        await update.message.reply_text("Henüz vücut ölçümü girmedin. /log_measurement ile başla!")
        return

    # Kilo
    weight_graph = plot_body_measurements(measurements, 'weight_kg', 'Kilo (kg)')
    if weight_graph and os.path.exists(weight_graph):
        await update.message.reply_photo(photo=open(weight_graph, 'rb'), caption="📉 Kilo Zaman İçinde")
        os.remove(weight_graph)

    # Bel
    waist_graph = plot_body_measurements(measurements, 'waist_cm', 'Bel Çevresi (cm)')
    if waist_graph and os.path.exists(waist_graph):
        await update.message.reply_photo(photo=open(waist_graph, 'rb'), caption="📏 Bel Çevresi Gelişimi")
        os.remove(waist_graph)

    await update.message.reply_text("✅ Tüm grafikler yüklendi! İlerlemeni takip etmeye devam et 💪")