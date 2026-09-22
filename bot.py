import os
import json
import time
import requests
import xml.etree.ElementTree as ET
import telebot
import re

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

def extract_media_and_text(description_html):
    """استخراج لینک تصویر و متن از محتوای فید"""
    img_match = re.search(r'<img[^>]+src="([^">]+)"', description_html)
    img_url = img_match.group(1) if img_match else None
    
    # حذف تگ‌های HTML برای به دست آوردن کپشن خالص
    clean_text = re.sub(r'<br\s*/?>', '\n', description_html)
    clean_text = re.sub(r'<[^>]+>', '', clean_text).strip()
    return img_url, clean_text

def get_posts_via_mirrors(username):
    """دریافت پست‌ها از چند سرور ضد بلاک"""
    mirrors = [
        f"https://rsshub.app/instagram/user/{username}",
        f"https://rss.app/feeds/public/instagram/{username}.xml",
        f"https://feed.eugeneyan.com/instagram/{username}",
        f"https://bibliogram.pussthecat.org/u/{username}/rss.xml"
    ]
    
    # تلاش با روش‌های دیگر در صورت نیاز
    for url in mirrors:
        try:
            print(f"در حال تلاش برای دریافت از: {url}")
            res = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200 and ("<rss" in res.text or "<feed" in res.text or "<xml" in res.text):
                root = ET.fromstring(res.content)
                posts = []
                for item in root.findall(".//item"):
                    guid = item.find("guid")
                    link = item.find("link")
                    desc = item.find("description")
                    
                    post_id = (guid.text if guid is not None and guid.text else (link.text if link is not None else ""))
                    post_id = post_id.strip().split("/")[-1].split("?")[0]
                    if not post_id:
                        continue
                        
                    html_content = desc.text if desc is not None and desc.text else ""
                    img_url, caption = extract_media_and_text(html_content)
                    
                    posts.append({
                        "id": post_id,
                        "image_url": img_url,
                        "caption": caption,
                        "link": f"https://www.instagram.com/p/{post_id}/"
                    })
                if posts:
                    print(f"موفقیت: {len(posts)} پست از سرور آینه‌ای دریافت شد.")
                    return posts
        except Exception as e:
            print(f"خطا در {url}: {e}")
            continue

    # اگر فیدها در دسترس نبودند، از متد مستقیم موبایل با پروکسی رایگان تست کن
    try:
        print("تلاش با متد دوم...")
        mobile_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        res = requests.get(mobile_url, headers={
            "User-Agent": "Instagram 219.0.0.12.117 Android",
            "Accept-Language": "en-US"
        }, timeout=15)
        if res.status_code == 200:
            data = res.json()
            items = data.get("graphql", {}).get("user", {}).get("edge_owner_to_timeline_media", {}).get("edges", [])
            posts = []
            for it in items:
                n = it.get("node", {})
                code = n.get("shortcode")
                cap_edges = n.get("edge_media_to_caption", {}).get("edges", [])
                cap = cap_edges[0]["node"]["text"] if cap_edges else ""
                posts.append({
                    "id": code,
                    "image_url": n.get("display_url"),
                    "caption": cap,
                    "link": f"https://www.instagram.com/p/{code}/"
                })
            return posts
    except Exception as e:
        print("خطا در متد دوم:", e)

    return []

print(f"شروع بررسی پست‌های پیج: {INSTA_USERNAME}")
posts = get_posts_via_mirrors(INSTA_USERNAME)

if not posts:
    print("متأسفانه اینستاگرام در این ساعت آی‌پی را محدود کرده است. در اجرای زمان‌بندی بعدی تلاش خواهد شد.")
    exit(0)

new_posts = [p for p in reversed(posts) if p["id"] not in posted_codes]
print(f"تعداد کل پست‌ها: {len(posts)} | پست‌های جدید برای ارسال: {len(new_posts)}")

for post in new_posts:
    caption = post["caption"]
    if len(caption) > 900:
        caption = caption[:900] + "..."
    caption += f"\n\n🔗 {post['link']}"

    try:
        if post["image_url"]:
            bot.send_photo(CHANNEL_ID, post["image_url"], caption=caption)
        else:
            bot.send_message(CHANNEL_ID, caption)
            
        print(f"پست {post['id']} با موفقیت به تلگرام ارسال شد.")
        posted_codes.append(post["id"])
        time.sleep(3)
    except Exception as e:
        print(f"خطا در ارسال به تلگرام: {e}")

# ذخیره تاریخچه
with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(posted_codes, f, ensure_ascii=False, indent=2)

print("عملیات پایان یافت.")
