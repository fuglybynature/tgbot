from telegram import Bot, Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
scheduler = BackgroundScheduler()

async def schedule_match_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/match command received from user {update.effective_user.id} with args: {context.args}")
    
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /match YYYY-MM-DD HH:MM Team1 - Team2")
        return

    try:
        date_str = context.args[0]
        time_str = context.args[1]
        comment = " ".join(context.args[2:])
        match_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        await update.message.reply_text("Invalid date/time format. Use: /match YYYY-MM-DD HH:MM Team1 - Team2")
        return

    reminder_time = match_dt - timedelta(minutes=30)

    if reminder_time <= datetime.now():
        await update.message.reply_text("⚠️ Match is too soon or already started.")
        logger.warning(f"Attempted to schedule match in the past: {match_dt}")
        return

    scheduler.add_job(
        send_reminder,
        'date',
        run_date=reminder_time,
        args=[update.effective_chat.id, comment]
    )

    logger.info(f"✅ Scheduled reminder for '{comment}' at {reminder_time.strftime('%Y-%m-%d %H:%M:%S')}")
    await update.message.reply_text(f"✅ Match reminder set for {match_dt.strftime('%Y-%m-%d %H:%M')} — \"{comment}\"")


def send_reminder(chat_id, comment):
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.info(f"⏰ Sending reminder: {comment} → chat_id={chat_id}")
    try:
        asyncio.run(bot.send_message(chat_id=chat_id, text=f"⏰ 30 minutes until match starts: {comment}"))
        logger.info("✅ Reminder sent successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to send reminder: {e}")
