import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from match_checker import get_next_matches
from config import TELEGRAM_TOKEN, CHAT_ID, MIN_TRANSFER_VALUE
from transfers_checker import fetch_transfers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start command received from user {update.effective_user.id}")
    welcome_text = (
        "Welcome! Here are the available commands:\n"
        "/start - Show this message\n"
        "/help - List commands\n"
        "/nextmatch <team> - Show next matches for a team\n"
        "/transfers - Show recent transfers over a minimum value"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/help command received from user {update.effective_user.id}")
    await start(update, context)

async def nextmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/nextmatch command received with args: {context.args} from user {update.effective_user.id}")
    if not context.args:
        await update.message.reply_text("Please provide a team name. Usage: /nextmatch Chelsea")
        return

    team_name = " ".join(context.args)
    matches = get_next_matches(team_name)

    if not matches:
        logger.info(f"No upcoming matches found for team '{team_name}'")
        await update.message.reply_text(f"No upcoming matches found for {team_name}.")
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
        await update.message.reply_text("⚠️ No recent transfers matching filter.")
        return
    await update.message.reply_text(message, parse_mode='Markdown')
    logging.info("Sent transfers message in /transfers command")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("nextmatch", nextmatch))
    app.add_handler(CommandHandler("transfers", transfers_command))

    logger.info("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
