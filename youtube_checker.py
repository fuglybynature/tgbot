import os
import requests
import logging
from datetime import datetime
from telegram import Bot

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Формат: {channel_id: last_video_id}
latest_video_ids = {}

# Канали з ENV, через кому
CHANNEL_IDS = os.getenv("YOUTUBE_CHANNEL_IDS", "").split(",")

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
            logger.info(f"No items found for channel {channel_id}")
            return None

        video = items[0]
        if video["id"]["kind"] != "youtube#video":
            logger.info(f"Latest item is not a video for channel {channel_id}")
            return None

        video_id = video["id"]["videoId"]
        title = video["snippet"]["title"]
        published_at = video["snippet"]["publishedAt"]
        published_at_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

        return {
            "video_id": video_id,
            "title": title,
            "published_at": published_at_dt,
        }

    except Exception as e:
        logger.error(f"Error fetching videos for channel {channel_id}: {e}")
        return None


def check_new_videos():
    logger.info("🔎 Checking YouTube channels for new videos...")
    bot = Bot(token=TELEGRAM_TOKEN)

    for channel_id in CHANNEL_IDS:
        channel_id = channel_id.strip()
        if not channel_id:
            continue

        video = get_latest_video(channel_id)
        if not video:
            logger.info(f"⚠️ No videos found for channel {channel_id}")
            continue

        last_seen_id = latest_video_ids.get(channel_id)
        if last_seen_id == video["video_id"]:
            logger.info(f"📼 No new video for channel {channel_id}. Latest ID unchanged.")
            continue

        latest_video_ids[channel_id] = video["video_id"]

        video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
        text = f"📺 New video: *{video['title']}*\n{video_url}"

        try:
            bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
            logger.info(f"✅ Sent video notification: {video_url}")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {e}")
