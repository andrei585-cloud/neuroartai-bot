#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, time, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or "8400229648:AAGsp41ZXNEaVNzV2WP0N-W0IqJ2sXCyimg"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
PROCESSED_FILE = "processed.txt"

print("[STARTUP] Bot ready")

# Загружаем обработанные сообщения с диска
def load_processed():
    """Load processed message IDs from disk"""
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        except:
            pass
    return set()

# Сохраняем новое обработанное сообщение
def save_processed(msg_key):
    """Save processed message ID to disk"""
    try:
        with open(PROCESSED_FILE, 'a') as f:
            f.write(msg_key + '\n')
    except:
        pass

processed = load_processed()
print(f"[LOAD] Loaded {len(processed)} processed messages from disk")

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
    global processed
    offset = 0
    
    while True:
        try:
            r = requests.post(f"{API_URL}/getUpdates", json={"offset": offset, "timeout": 30}, timeout=35)
            if r.status_code != 200:
                time.sleep(1)
                continue
            
            updates = r.json().get("result", [])
            if not updates:
                time.sleep(0.5)
                continue
            
            for upd in updates:
                offset = upd.get("update_id", 0) + 1
                msg = upd.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "").strip()
                msg_id = msg.get("message_id")
                
                if not (chat_id and text and msg_id):
                    continue
                
                # Дедупликация - проверяем с диска
                key = f"{chat_id}_{msg_id}"
                if key in processed:
                    print(f"[SKIP] Duplicate: {key}")
                    continue
                
                # Помечаем как обработанное И СОХРАНЯЕМ НА ДИСК
                processed.add(key)
                save_processed(key)
                print(f"[MSG] {chat_id}: {text[:40]}")
                
                # Обработка
                if text == "/start":
                    send_msg(chat_id, "Hi! Send me a description and I'll generate an image 🎨")
                    continue
                
                # Генерируем изображение для любого текста
                send_msg(chat_id, f"⏳ Generating... ({text[:40]})")
                img = gen_img(text)
                
                if img:
                    Path("images").mkdir(exist_ok=True)
                    fn = f"images/img_{chat_id}_{int(time.time())}.png"
                    with open(fn, 'wb') as f:
                        f.write(img)
                    send_photo(chat_id, fn, f"Generated: {text[:60]}")
                else:
                    send_msg(chat_id, "❌ Generation failed. Try again.")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()

