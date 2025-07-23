import os
import requests
import logging
from datetime import datetime
from telegram import Bot
from html import escape

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Словник для кешу останніх відео
latest_video_ids = {}

# Список каналів, що моніторяться
CHANNEL_IDS = os.getenv("CHANNEL_IDS", "").split(",")

logger = logging.getLogger(__name__)


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
        resp = requests.get(url)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            logger.warning(f"No items returned for channel {channel_id}")
            return None

        video = items[0]
        if video["id"]["kind"] != "youtube#video":
            return None

        return {
            "video_id": video["id"]["videoId"],
            "title": video["snippet"]["title"],
            "published_at": datetime.fromisoformat(video["snippet"]["publishedAt"].replace("Z", "+00:00"))
        }

    except Exception as e:
        logger.error(f"Error fetching videos for channel {channel_id}: {e}")
        return None


async def check_new_videos():
    logger.info("⏱️ Checking YouTube channels for new videos...")
    bot = Bot(token=TELEGRAM_TOKEN)

    for channel_id in CHANNEL_IDS:
        video = get_latest_video(channel_id)
        if not video:
            continue

        last_seen_id = latest_video_ids.get(channel_id)
        if last_seen_id == video["video_id"]:
            continue  # Те саме відео

        latest_video_ids[channel_id] = video["video_id"]

        video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
        title_html = escape(video["title"])
        text = f"📺 New video: <b>{title_html}</b>\n{video_url}"

        try:
            await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
            logger.info(f"✅ Sent video notification: {video_url}")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message for video {video_url}: {e}")
