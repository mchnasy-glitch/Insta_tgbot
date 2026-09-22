import os
import json
import time
import requests
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
        posted_codes = []

def get_instagram_posts(username):
    """استفاده از API سبک و مستقیم برای خواندن آخرین پست‌های پیج عمومی"""
    s = requests.Session()
    
    # تنظیم هدرهای کاملاً طبیعی مرورگر
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    })
    
    # روش اول: استفاده از سرویس رایگان و پایدار Picuki API
    try:
        print(f"تلاش از طریق سرور Picuki...")
        url = f"https://www.picuki.com/profile/{username}"
        res = s.get(url, timeout=15)
        if res.status_code == 200 and "post-wrapper" in res.text:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.find_all("div", class_="post-wrapper")
            
            posts = []
            for item in items[:4]:
                a_tag = item.find("a")
                img_tag = item.find("img")
                desc_tag = item.find("div", class_="post-description")
                
                if not a_tag:
                    continue
                
                link = a_tag.get("href", "")
                post_id = link.strip("/").split("/")[-1]
                img_url = img_tag.get("src", "") if img_tag else ""
                caption = desc_tag.text.strip() if desc_tag else ""
                
                posts.append({
                    "id": post_id,
                    "image_url": img_url,
                    "caption": caption,
                    "link": f"https://www.instagram.com/p/{post_id}/"
                })
            if posts:
                print(f"موفق: {len(posts)} پست از طریق سرور پیدا شد.")
                return posts
    except Exception as e:
        print("خطا در روش اول:", e)

    # روش دوم: فید استاندارد بدون مسدودسازی (RSSHub با آی‌پی‌های چرخان)
    try:
        print("تلاش از طریق گره‌های RSSHub...")
        rss_urls = [
            f"https://rsshub.app/instagram/user/{username}",
            f"https://rsshub.rssforever.com/instagram/user/{username}",
            f"https://rsshub.moeyao.com/instagram/user/{username}"
        ]
        import xml.etree.ElementTree as ET
        import re
        for r_url in rss_urls:
            try:
                r = requests.get(r_url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200 and "<item>" in r.text:
                    root = ET.fromstring(r.content)
                    posts = []
                    for item in root.findall(".//item")[:4]:
                        guid = item.find("guid")
                        desc = item.find("description")
                        p_id = guid.text.split("/")[-1] if guid is not None else str(time.time())
                        
                        desc_text = desc.text if desc is not None else ""
                        img_match = re.search(r'src="([^"]+)"', desc_text)
                        img_url = img_match.group(1) if img_match else ""
                        
                        clean_caption = re.sub(r'<[^>]+>', '', desc_text).strip()
                        
                        posts.append({
                            "id": p_id,
                            "image_url": img_url,
                            "caption": clean_caption,
                            "link": f"https://www.instagram.com/p/{p_id}/"
                        })
                    if posts:
                        print(f"موفق: {len(posts)} پست از طریق گره RSS پیدا شد.")
                        return posts
            except Exception:
                continue
    except Exception as e:
        print("خطا در روش دوم:", e)

    return []

print(f"شروع بررسی پیج {INSTA_USERNAME}...")
posts = get_instagram_posts(INSTA_USERNAME)

if not posts:
    print("در حال حاضر پست جدیدی دریافت نشد.")
    exit(0)

new_posts = [p for p in reversed(posts) if p["id"] not in posted_codes]
print(f"تعداد کل پست‌ها: {len(posts)} | جدید: {len(new_posts)}")

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
            
        print(f"پست {post['id']} با موفقیت به تلگرام ارسال شد.")
        posted_codes.append(post["id"])
        time.sleep(3)
    except Exception as e:
        print(f"خطا در ارسال به تلگرام: {e}")

# ذخیره تاریخچه
with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(posted_codes, f, ensure_ascii=False, indent=2)

print("پایان عملیات.")
