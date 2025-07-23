# youtube_checker.py

import os
import requests
import logging
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep

# ENV змінні
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_IDS = os.getenv("YOUTUBE_CHANNEL_IDS", "").split(",")
CHANNEL_IDS = [ch.strip() for ch in CHANNEL_IDS if ch.strip()]

# Логер
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Статус останніх відео
latest_video_ids = {}

def get_latest_video(channel_id):
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?key={YOUTUBE_API_KEY}"
        f"&channelId={channel_id}"
        f"&part=snippet"
        f"&order=date"
        f"&maxResults=1"
    )

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return None

        video = items[0]
        if video["id"]["kind"] != "youtube#video":
            return None

        return {
            "video_id": video["id"]["videoId"],
            "title": video["snippet"]["title"],
            "published_at": video["snippet"]["publishedAt"],
        }

    except Exception as e:
        logger.error(f"❌ Error fetching video for {channel_id}: {e}")
        return None


def check_new_videos():
    logger.info("🔍 Checking YouTube channels for new videos...")
    bot = Bot(token=TELEGRAM_TOKEN)

    for channel_id in CHANNEL_IDS:
        video = get_latest_video(channel_id)
        if not video:
            continue

        last_seen_id = latest_video_ids.get(channel_id)
        if last_seen_id == video["video_id"]:
            continue  # те саме відео, що минулого разу

        latest_video_ids[channel_id] = video["video_id"]

        video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
        text = f"📺 New video: *{video['title']}*\n{video_url}"

        try:
            bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
            logger.info(f"✅ Sent notification: {video_url}")
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")


def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_new_videos, "interval", minutes=10)
    scheduler.start()
    logger.info("✅ YouTube checker started (interval: 10 minutes)")

    try:
        while True:
            sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("🛑 YouTube checker stopped.")


if __name__ == "__main__":
    main()
