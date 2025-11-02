#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, time, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or "8400229648:AAGsp41ZXNEaVNzV2WP0N-W0IqJ2sXCyimg"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
OFFSET_FILE = "offset.txt"

print("[STARTUP] Bot ready")

# Загружаем последний offset
def load_offset():
    """Load last processed offset from disk"""
    if os.path.exists(OFFSET_FILE):
        try:
            with open(OFFSET_FILE, 'r') as f:
                val = f.read().strip()
                if val.isdigit():
                    return int(val)
        except:
            pass
    return 0

# Сохраняем новый offset
def save_offset(offset):
    """Save offset to disk"""
    try:
        with open(OFFSET_FILE, 'w') as f:
            f.write(str(offset))
    except:
        pass

offset = load_offset()
print(f"[LOAD] Starting with offset={offset}")

def send_msg(chat_id, text):
    """Send message"""
    try:
        requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def send_photo(chat_id, img_path, cap):
    """Send photo"""
    try:
        with open(img_path, 'rb') as f:
            requests.post(f"{API_URL}/sendPhoto", files={'photo': f}, data={'chat_id': chat_id, 'caption': cap}, timeout=60)
    except:
        pass

def gen_img(prompt):
    """Generate image"""
    try:
        import urllib.parse
        safe_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}"
        r = requests.get(url, timeout=120, allow_redirects=True)
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
    except:
        pass
    return None

def main():
    global offset
    
    while True:
        try:
            r = requests.post(f"{API_URL}/getUpdates", json={"offset": offset, "timeout": 30}, timeout=35)
            if r.status_code != 200:
                print(f"[POLL ERROR] Status {r.status_code}")
                time.sleep(1)
                continue
            
            updates = r.json().get("result", [])
            print(f"[POLL] Got {len(updates)} updates")
            
            if not updates:
                time.sleep(0.5)
                continue
            
            for upd in updates:
                update_id = upd.get("update_id", 0)
                msg = upd.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "").strip()
                msg_id = msg.get("message_id")
                
                if not (chat_id and text and msg_id):
                    offset = update_id + 1
                    save_offset(offset)
                    continue
                
                print(f"[MSG] chat={chat_id}, msg_id={msg_id}, text={text[:30]}")
                
                # Обработка
                if text == "/start":
                    send_msg(chat_id, "Hi! Send me a description and I'll generate an image 🎨")
                else:
                    # Генерируем изображение для любого текста
                    print(f"[GEN] Starting generation for: {text[:40]}")
                    send_msg(chat_id, f"⏳ Generating... ({text[:40]})")
                    img = gen_img(text)
                    
                    if img:
                        Path("images").mkdir(exist_ok=True)
                        fn = f"images/img_{chat_id}_{int(time.time())}.png"
                        with open(fn, 'wb') as f:
                            f.write(img)
                        print(f"[SEND] Photo: {fn}")
                        send_photo(chat_id, fn, f"Generated: {text[:60]}")
                    else:
                        print(f"[FAIL] Generation failed")
                        send_msg(chat_id, "❌ Generation failed. Try again.")
                
                # Обновляем offset ПОСЛЕ обработки сообщения
                offset = update_id + 1
                save_offset(offset)
                print(f"[SAVE] offset={offset}")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()

