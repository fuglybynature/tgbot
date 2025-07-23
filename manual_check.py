import asyncio
import logging
import os
from youtube_checker import check_new_videos, CHANNEL_IDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_manual_check():
    logger.info("🚀 Starting manual YouTube check...")

    # Перевіримо, чи є канали
    if not CHANNEL_IDS:
        logger.warning("⚠️ No CHANNEL_IDS found in environment.")
        return

    logger.info(f"🔢 Loaded {len(CHANNEL_IDS)} channels:")
    for i, cid in enumerate(CHANNEL_IDS, start=1):
        logger.info(f"   {i}. {cid}")

    # Запускаємо перевірку
    try:
        await check_new_videos()
        logger.info("✅ check_new_videos completed without exception.")
    except Exception as e:
        logger.error(f"❌ Exception occurred during check: {e}")

    logger.info("🏁 Manual check finished.")


if __name__ == "__main__":
    asyncio.run(run_manual_check())
