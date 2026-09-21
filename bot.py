import os
import time
import json
import telebot
import instaloader

TELEGRAM_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TG_CHANNEL_ID")
TARGET_PAGE = "alacharm_meraj"
HISTORY_FILE = "posted_shortcodes.json"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")
L = instaloader.Instaloader(
    download_pictures=True,
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    save_metadata=False
)

# بارگذاری تاریخچه پست‌های قبلی
posted = []
if os.path.exists(HISTORY_FILE):
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted = json.load(f)
    except:
        posted = []

try:
    profile = instaloader.Profile.from_username(L.context, TARGET_PAGE)
    # بررسی ۵ پست آخر برای سرعت بالا
    for post in profile.get_posts():
        if post.shortcode in posted:
            continue
        
        caption = (post.caption or "") + f"\n\n🆔 {TELEGRAM_CHANNEL_ID}"
        # محدودیت تلگرام برای کپشن ۱۰۲۴ کاراکتر است
        if len(caption) > 1000:
            caption = caption[:990] + "..."

        if post.is_video:
            bot.send_video(TELEGRAM_CHANNEL_ID, post.video_url, caption=caption)
        else:
            bot.send_photo(TELEGRAM_CHANNEL_ID, post.url, caption=caption)

        posted.append(post.shortcode)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(posted[-100:], f)
        
        time.sleep(3)
        break  # در هر نوبت آخرین پست جدید را می‌فرستد
except Exception as e:
    print(f"Error: {e}")
