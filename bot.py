import os
import json
import time
import instaloader
import telebot

BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TG_CHANNEL_ID")
INSTA_USERNAME = "alacharm_meraj"
HISTORY_FILE = "posted_shortcodes.json"

if not BOT_TOKEN or not CHANNEL_ID:
    print("خطا: توکن ربات یا آیدی کانال تنظیم نشده است!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# خواندن تاریخچه پست‌های قبلی
posted_codes = []
if os.path.exists(HISTORY_FILE):
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_codes = json.load(f)
    except Exception as e:
        print("خطا در خواندن فایل تاریخچه:", e)
        posted_codes = []

# تنظیم Instaloader با تنظیمات امن برای گیت‌هاب
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
)

print(f"در حال دریافت اطلاعات پیج: {INSTA_USERNAME}")

new_posts_to_send = []

try:
    profile = instaloader.Profile.from_username(L.context, INSTA_USERNAME)
    print(f"پیج با موفقیت پیدا شد: {profile.full_name} ({profile.mediacount} پست)")
    
    # فقط ۳ پست آخر را بررسی کن تا سرعت بالا باشد و اینستاگرام بلاک نکند
    count = 0
    for post in profile.get_posts():
        if count >= 3:
            break
        count += 1
        
        shortcode = post.shortcode
        if shortcode not in posted_codes:
            new_posts_to_send.append({
                "shortcode": shortcode,
                "is_video": post.is_video,
                "video_url": post.video_url if post.is_video else None,
                "image_url": post.url,
                "caption": post.caption or ""
            })
            
except Exception as e:
    print("خطا در دریافت پست‌ها از طریق Instaloader:", e)

print(f"تعداد پست‌های جدید برای ارسال: {len(new_posts_to_send)}")

# ارسال پست‌ها از قدیمی‌تر به جدیدتر
for post in reversed(new_posts_to_send):
    caption = post["caption"]
    if len(caption) > 900:
        caption = caption[:900] + "..."
    caption += f"\n\n🔗 instagram.com/p/{post['shortcode']}/"

    try:
        if post["is_video"] and post["video_url"]:
            bot.send_video(CHANNEL_ID, post["video_url"], caption=caption)
        elif post["image_url"]:
            bot.send_photo(CHANNEL_ID, post["image_url"], caption=caption)
            
        print(f"پست {post['shortcode']} با موفقیت به کانال ارسال شد.")
        posted_codes.append(post["shortcode"])
        time.sleep(3)
    except Exception as e:
        print(f"خطا در ارسال پست {post['shortcode']} به تلگرام:", e)

# ذخیره تاریخچه
with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(posted_codes, f, ensure_ascii=False, indent=2)

print("عملیات پایان یافت.")
