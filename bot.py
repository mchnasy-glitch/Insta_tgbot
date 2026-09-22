import os
import json
import time
import requests
import telebot

# پیکربندی متغیرها
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TG_CHANNEL_ID")
INSTA_USERNAME = "alacharm_meraj"  # آیدی دقیق بدون فاصله
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

def fetch_instagram_posts(username):
    """دریافت پست‌های اینستاگرام با هدرهای شبیه‌ساز مرورگر واقعی"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
        "X-IG-App-ID": "936619743392459",
        "Referer": f"https://www.instagram.com/{username}/",
    }
    
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            user_data = data.get("data", {}).get("user", {})
            edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
            
            posts = []
            for item in edges:
                node = item.get("node", {})
                shortcode = node.get("shortcode")
                is_video = node.get("is_video", False)
                video_url = node.get("video_url")
                display_url = node.get("display_url")
                
                # کپشن پست
                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                caption = caption_edges[0]["node"]["text"] if caption_edges else ""
                
                posts.append({
                    "shortcode": shortcode,
                    "is_video": is_video,
                    "video_url": video_url,
                    "image_url": display_url,
                    "caption": caption
                })
            return posts
        else:
            print(f"Instagram API Error: {resp.status_code} - {resp.text[:150]}")
    except Exception as exc:
        print("خطا در برقراری ارتباط با اینستاگرام:", exc)

    return []

print(f"در حال بررسی پیج: {INSTA_USERNAME}")
posts = fetch_instagram_posts(INSTA_USERNAME)

if not posts:
    print("پستی دریافت نشد یا پیج موقتاً توسط اینستاگرام مسدود شده است.")
    exit(0)

# بررسی از قدیمی به جدید برای حفظ ترتیب
new_posts = [p for p in reversed(posts) if p["shortcode"] not in posted_codes]

print(f"تعداد کل پست‌های بررسی‌شده: {len(posts)}")
print(f"پست‌های جدید: {len(new_posts)}")

for post in new_posts:
    caption = post["caption"]
    if len(caption) > 950:
        caption = caption[:950] + "..."
    caption += f"\n\n🔗 instagram.com/p/{post['shortcode']}/"

    try:
        if post["is_video"] and post["video_url"]:
            bot.send_video(CHANNEL_ID, post["video_url"], caption=caption)
        elif post["image_url"]:
            bot.send_photo(CHANNEL_ID, post["image_url"], caption=caption)
            
        print(f"پست با کد {post['shortcode']} با موفقیت به تلگرام ارسال شد.")
        posted_codes.append(post["shortcode"])
        time.sleep(3)
    except Exception as e:
        print(f"خطا در ارسال پست {post['shortcode']} به تلگرام:", e)

# ذخیره تاریخچه جدید
with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(posted_codes, f, ensure_ascii=False, indent=2)

print("پایان عملیات همگام‌سازی.")
