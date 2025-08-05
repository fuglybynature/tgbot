# match_reminder.py

from telegram import Bot, Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os
import asyncio
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("match_reminder")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
KYIV_TZ = pytz.timezone("Europe/Kyiv")
scheduler = BackgroundScheduler(timezone=KYIV_TZ)

# Збереження запланованих матчів у памʼяті
scheduled_reminders = []

async def schedule_match_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/match command received from user {update.effective_user.id} with args: {context.args}")

    if len(context.args) < 3:
        await update.message.reply_text("Формат: /match РРРР-ММ-ДД ГГ:ХХ Коментар")
        return

    try:
        date_str = context.args[0]
        time_str = context.args[1]
        comment = " ".join(context.args[2:])
        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        match_dt = KYIV_TZ.localize(naive_dt)
    except ValueError:
        await update.message.reply_text("Невірний формат дати/часу. Використовуйте: /match РРРР-ММ-ДД ГГ:ХХ Коментар")
        return

    reminder_time = match_dt - timedelta(minutes=30)
    now = datetime.now(KYIV_TZ)

    if reminder_time <= now:
        await update.message.reply_text("⚠️ Матч уже почався або надто близько до поточного часу.")
        return

    reminder_id = len(scheduled_reminders) + 1
    job = scheduler.add_job(
        send_reminder,
        'date',
        run_date=reminder_time,
        args=[update.effective_chat.id, comment]
    )

    scheduled_reminders.append({
        "id": reminder_id,
        "chat_id": update.effective_chat.id,
        "match_time": match_dt,
        "comment": comment,
        "job": job
    })

    await update.message.reply_text(f"✅ Нагадування заплановано на {match_dt.strftime('%Y-%m-%d %H:%M')} — '{comment}' (ID: {reminder_id})")


async def list_reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not scheduled_reminders:
        await update.message.reply_text("ℹ️ Немає запланованих нагадувань.")
        return

    text = "📋 Заплановані нагадування:\n"
    for r in scheduled_reminders:
        text += f"{r['id']}. {r['match_time'].strftime('%Y-%m-%d %H:%M')} — {r['comment']}\n"

    await update.message.reply_text(text)


async def remove_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Використання: /removereminder <ID>")
        return

    reminder_id = int(context.args[0])
    reminder = next((r for r in scheduled_reminders if r["id"] == reminder_id), None)

    if not reminder:
        await update.message.reply_text(f"❌ Нагадування з ID {reminder_id} не знайдено.")
        return

    reminder["job"].remove()
    scheduled_reminders.remove(reminder)
    await update.message.reply_text(f"✅ Нагадування ID {reminder_id} видалено.")


def send_reminder(chat_id, comment):
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        asyncio.run(bot.send_message(chat_id=chat_id, text=f"⏰ До початку матчу залишилось 30 хв: {comment}"))
    except Exception as e:
        logger.error(f"❌ Помилка при надсиланні нагадування: {e}")
