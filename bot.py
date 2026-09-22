import os
import json
import time
import requests
from bs4 import BeautifulSoup
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

def get_posts_via_imginn(username):
    """استفاده از آینه‌های اینستاگرام برای دور زدن محدودیت ۴۲۹"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    services = [
        f"https://imginn.com/{username}/",
        f"https://dumpoir.com/v/{username}"
    ]
    
    posts = []
    
    for url in services:
        try:
            print(f"در حال تلاش برای دریافت از: {url}")
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # خواندن ساختار Imginn
                items = soup.find_all("div", class_="item")
                if not items:
                    items = soup.find_all("div", class_="media-item")
                    
                for item in items[:4]:
                    a_tag = item.find("a")
                    img_tag = item.find("img")
                    if not a_tag:
                        continue
                        
                    href = a_tag.get("href", "")
                    # استخراج آیدی یا کد پست
                    post_id = href.strip("/").split("/")[-1]
                    
                    img_url = ""
                    if img_tag:
                        img_url = img_tag.get("data-src") or img_tag.get("src") or ""
                        
                    desc = item.find("div", class_="desc")
                    caption = desc.text.strip() if desc else ""
                    
                    if post_id and (post_id not in [p["id"] for p in posts]):
                        posts.append({
                            "id": post_id,
                            "image_url": img_url,
                            "caption": caption,
                            "link": f"https://www.instagram.com/p/{post_id}/"
                        })
                        
                if posts:
                    print(f"موفقیت: {len(posts)} پست پیدا شد.")
                    return posts
        except Exception as e:
            print(f"خطا در سرویس {url}: {e}")
            continue
            
    return posts

print(f"شروع بررسی پیج {INSTA_USERNAME}...")
posts = get_posts_via_imginn(INSTA_USERNAME)

if not posts:
    print("هیچ پستی یافت نشد. در نوبت بعدی بررسی خواهد شد.")
    exit(0)

# جداسازی پست‌های جدید
new_posts = [p for p in reversed(posts) if p["id"] not in posted_codes]
print(f"تعداد کل پست‌ها: {len(posts)} | پست‌های جدید: {len(new_posts)}")

for post in new_posts:
    caption = post["caption"]
    if len(caption) > 900:
        caption = caption[:900] + "..."
    caption += f"\n\n🔗 {post['link']}"

    try:
        if post["image_url"] and post["image_url"].startswith("http"):
            bot.send_photo(CHANNEL_ID, post["image_url"], caption=caption)
        else:
            bot.send_message(CHANNEL_ID, caption)
            
        print(f"پست {post['id']} با موفقیت به تلگرام فرستاده شد.")
        posted_codes.append(post["id"])
        time.sleep(3)
    except Exception as e:
        print(f"خطا در ارسال پست {post['id']}: {e}")

# ذخیره تاریخچه
with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(posted_codes, f, ensure_ascii=False, indent=2)

print("پایان عملیات.")
