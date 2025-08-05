import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

from match_checker import get_next_matches
from transfers_checker import fetch_transfers
from youtube_checker import check_new_videos

from match_reminder import (
    schedule_match_command,
    list_reminders_command,
    remove_reminder_command,
    scheduler
)

from openai import AsyncOpenAI

client = AsyncOpenAI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start command received from user {update.effective_user.id}")
    welcome_text = (
        "👋 Вітаю! Доступні команди:\n"
        "/start — Показати це повідомлення\n"
        "/help — Допомога\n"
        "/nextmatch <команда> — Показати наступні матчі для команди\n"
        "/transfers — Показати останні трансфери\n"
        "/ask <питання> — Запитати щось у ШІ\n"
        "/match <дата> <час> <коментар> — Додати нагадування за 30 хв до матчу\n"
        "/listreminders — Показати всі заплановані нагадування\n"
        "/removereminder <ID> — Видалити нагадування за ID"
    )
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/help command received from user {update.effective_user.id}")
    await start(update, context)


async def nextmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/nextmatch command received with args: {context.args} from user {update.effective_user.id}")
    if not context.args:
        await update.message.reply_text("Введіть назву команди. Приклад: /nextmatch Chelsea")
        return

    team_name = " ".join(context.args)
    matches = get_next_matches(team_name)

    if not matches:
        logger.info(f"No upcoming matches found for team '{team_name}'")
        await update.message.reply_text(f"Немає запланованих матчів для {team_name}.")
        return

    response = ""
    for m in matches:
        response += f"{m['date']} {m['time']} — {m['home']} vs {m['away']} ({m['league']})\n"

    await update.message.reply_text(response.strip())
    logger.info(f"Sent next matches info for team '{team_name}'")


async def transfers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"/transfers command received from user {update.effective_user.id}")
    message = fetch_transfers(limit=10)
    if not message:
        logging.info("No transfers found matching filter on /transfers command")
        await update.message.reply_text("⚠️ Немає трансферів, що відповідають фільтру.")
        return
    await update.message.reply_text(message, parse_mode='Markdown')
    logging.info("Sent transfers message in /transfers command")


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/ask command received from user {update.effective_user.id} with args: {context.args}")
    if not context.args:
        await update.message.reply_text("Введіть питання. Приклад: /ask Що таке офсайд?")
        return

    prompt = " ".join(context.args)

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7,
        )
        reply_text = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        reply_text = "⚠️ Помилка при зверненні до OpenAI."

    await update.message.reply_text(reply_text)


# 🔧 Обгортка для YouTube перевірок
def run_youtube_check():
    asyncio.run(check_new_videos())


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("nextmatch", nextmatch))
    app.add_handler(CommandHandler("transfers", transfers_command))
    app.add_handler(CommandHandler("ask", ask_command))

    # Нагадування
    app.add_handler(CommandHandler("match", schedule_match_command))
    app.add_handler(CommandHandler("listreminders", list_reminders_command))
    app.add_handler(CommandHandler("removereminder", remove_reminder_command))

    logger.info("✅ Бот запущено...")

    scheduler.start()
    scheduler.add_job(run_youtube_check, "interval", hours=3)

    app.run_polling()


if __name__ == "__main__":
    main()
