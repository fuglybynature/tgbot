from telegram import Bot, Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os
import asyncio
import pytz  # ⬅️ потрібно встановити: pip install pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
scheduler = BackgroundScheduler()

KYIV_TZ = pytz.timezone("Europe/Kyiv")  # ⬅️ твоя локальна зона

async def schedule_match_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/match command received from user {update.effective_user.id} with args: {context.args}")
    
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /match YYYY-MM-DD HH:MM Team1 - Team2")
        return

    try:
        date_str = context.args[0]
        time_str = context.args[1]
        comment = " ".join(context.args[2:])
        
        # парсимо локальний час
        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        match_dt = KYIV_TZ.localize(naive_dt)

    except ValueError:
        await update.message.reply_text("Invalid date/time format. Use: /match YYYY-MM-DD HH:MM Team1 - Team2")
        return

    reminder_time = match_dt - timedelta(minutes=30)
    now = datetime.now(KYIV_TZ)

    logger.info(f"📆 Parsed match time (Kyiv TZ): {match_dt}")
    logger.info(f"🕒 Current time (Kyiv TZ): {now}")
    logger.info(f"⏰ Reminder scheduled for: {reminder_time}")

    if reminder_time <= now:
        await update.message.reply_text("⚠️ Match is too soon or already started.")
        logger.warning(f"Attempted to schedule match in the past: {match_dt}")
        return

    scheduler.add_job(
        send_reminder,
        'date',
        run_date=reminder_time,
        args=[update.effective_chat.id, comment]
    )

    logger.info(f"✅ Scheduled reminder for '{comment}' at {reminder_time}")
    await update.message.reply_text(f"✅ Match reminder set for {match_dt.strftime('%Y-%m-%d %H:%M')} — \"{comment}\"")


def send_reminder(chat_id, comment):
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.info(f"⏰ Sending reminder: {comment} → chat_id={chat_id}")
    try:
        asyncio.run(bot.send_message(chat_id=chat_id, text=f"⏰ 30 minutes until match starts: {comment}"))
        logger.info("✅ Reminder sent successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to send reminder: {e}")
