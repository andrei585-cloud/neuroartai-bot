#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroArtAI Bot with Authorization, Menu & Daily Limits
"""
import os, json, time, requests, re
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# На локальной машине используем .env, на Railway используем переменные окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Если TELEGRAM_TOKEN не найден - используем значение по умолчанию (для Railway)
if not TELEGRAM_TOKEN:
    # Fallback для Railway если переменные не работают
    TELEGRAM_TOKEN = "8400229648:AAGsp41ZXNEaVNzV2WP0N-W0IqJ2sXCyimg"
    print("[INFO] Using hardcoded TELEGRAM_TOKEN (Railway fallback)")

if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TOKEN_HERE":
    print("ERROR: TELEGRAM_TOKEN not configured!")
    print("Set environment variable TELEGRAM_TOKEN on Railway or update bot.py")
    exit(1)

ADMIN_ID = 552195777

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
DATA_DIR = Path("data/emails")
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("[STARTUP] Bot initialized with Auth & Menus")
print(f"[INFO] Using Telegram Token: {TELEGRAM_TOKEN[:20]}...")

# ==================== Setup Bot Commands ====================

def setup_commands():
    """Register bot commands in Telegram"""
    commands = [
        {"command": "start", "description": "Начать работу с ботом"},
        {"command": "profile", "description": "Мой профиль и статистика"},
        {"command": "generate", "description": "Генерировать изображение"},
        {"command": "help", "description": "Справка"},
    ]
    try:
        requests.post(f"{API_URL}/setMyCommands", json={"commands": commands}, timeout=10)
        print("[SETUP] Commands registered")
    except:
        pass

# ==================== Storage Functions ====================

def get_user_file(chat_id):
    """Get user data file path"""
    return DATA_DIR / f"{chat_id}.json"

def get_user_data(chat_id):
    """Load user data from file"""
    try:
        f = get_user_file(chat_id)
        if f.exists():
            return json.loads(f.read_text())
    except:
        pass
    return None

def save_user_data(chat_id, email):
    """Save user data to file"""
    try:
        data = {
            "email": email,
            "chat_id": chat_id,
            "created": datetime.now().isoformat(),
            "today": datetime.now().date().isoformat(),
            "count": 0
        }
        get_user_file(chat_id).write_text(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"[SAVE ERROR] {e}")
    return False

def is_authorized(chat_id):
    """Check if user is authorized"""
    if chat_id == ADMIN_ID:
        return True
    return get_user_data(chat_id) is not None

def get_generation_count(chat_id):
    """Get today's generation count"""
    if chat_id == ADMIN_ID:
        return 0, 999
    
    data = get_user_data(chat_id)
    if not data:
        return 0, 10
    
    today = datetime.now().date().isoformat()
    if data.get("today") != today:
        data["today"] = today
        data["count"] = 0
        get_user_file(chat_id).write_text(json.dumps(data, indent=2))
    
    return data.get("count", 0), 10

def increment_count(chat_id):
    """Increment generation count"""
    if chat_id == ADMIN_ID:
        return
    
    data = get_user_data(chat_id)
    if data:
        data["count"] = data.get("count", 0) + 1
        get_user_file(chat_id).write_text(json.dumps(data, indent=2))

def validate_email(email):
    """Check email format"""
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def email_exists(email):
    """Check if email already registered"""
    for f in DATA_DIR.glob("*.json"):
        try:
            if json.loads(f.read_text()).get("email") == email:
                return True
        except:
            pass
    return False

# ==================== Telegram Functions ====================

def send_msg(chat_id, text, keyboard=None):
    """Send text message with optional keyboard"""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    
    if keyboard:
        payload["reply_markup"] = {
            "keyboard": keyboard,
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    
    try:
        requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
    except:
        pass

def send_img(chat_id, img_path, cap):
    """Send image with caption"""
    for _ in range(3):
        try:
            with open(img_path, 'rb') as f:
                r = requests.post(f"{API_URL}/sendPhoto", 
                    files={'photo': f}, 
                    data={'chat_id': chat_id, 'caption': cap, 'parse_mode': 'HTML'}, 
                    timeout=60)
                if r.status_code == 200:
                    return True
        except:
            time.sleep(1)
    return False

def gen_img(prompt):
    """Generate image using Pollinations API"""
    try:
        import urllib.parse
        safe_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}"
        r = requests.get(url, timeout=120, allow_redirects=True)
        
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
    except Exception as e:
        print(f"[GEN ERROR] {str(e)[:50]}")
    
    return None

# ==================== Main Bot Logic ====================

processed = set()
waiting_email = {}
waiting_prompt = {}

def main_menu_keyboard():
    """Get main menu keyboard"""
    return [
        ["🎨 Генерировать", "📧 Мой аккаунт"],
        ["ℹ️ Помощь"]
    ]

def auth_keyboard():
    """Get auth keyboard"""
    return [["📧 Авторизоваться по email"]]

def handle(chat_id, text):
    """Handle incoming message"""
    
    # START
    if text == "/start":
        if is_authorized(chat_id):
            send_msg(chat_id, "👋 Добро пожаловать! Выбери действие:", main_menu_keyboard())
        else:
            send_msg(chat_id, "👋 Добро пожаловать в NeuroArtAI!\nДля начала авторизуйся.", auth_keyboard())
        return
    
    # PROFILE
    if text == "/profile":
        data = get_user_data(chat_id)
        count, limit = get_generation_count(chat_id)
        
        if chat_id == ADMIN_ID:
            send_msg(chat_id, f"👤 <b>Админ аккаунт</b>\n\n🔑 ID: {ADMIN_ID}\n📊 Статус: НЕОГРАНИЧЕННЫЙ\n\nВыбери действие:", main_menu_keyboard())
        elif data:
            send_msg(chat_id, f"👤 <b>Информация аккаунта:</b>\n📧 Email: {data['email']}\n📊 Генераций сегодня: {count}/{limit}\n📅 Дата регистрации: {data['created'][:10]}\n\nВыбери действие:", main_menu_keyboard())
        else:
            send_msg(chat_id, "❌ Не авторизован. Используй /start")
        return
    
    # GENERATE COMMAND
    if text == "/generate":
        if not is_authorized(chat_id):
            send_msg(chat_id, "❌ Авторизуйся сначала! /start")
            return
        
        count, limit = get_generation_count(chat_id)
        if count >= limit:
            send_msg(chat_id, f"❌ Лимит достигнут! ({limit}/{limit})\nПопробуй завтра.")
            return
        
        if chat_id in waiting_prompt:
            return
        
        waiting_prompt[chat_id] = True
        send_msg(chat_id, f"🎨 Опиши изображение (сегодня: {count}/{limit}):")
        return
    
    # HELP COMMAND
    if text == "/help":
        send_msg(chat_id, "🤖 <b>NeuroArtAI Bot</b>\n\n<b>Команды:</b>\n/start - Начать\n/profile - Профиль\n/generate - Генерировать\n/help - Справка\n\n<b>Функции:</b>\n📸 Генерируй AI изображения\n📧 Один email = один аккаунт\n⏰ Лимит: 10 в день\n\n<b>Кнопки меню ниже 👇</b>", main_menu_keyboard())
        return
    
    # AUTHORIZE BY EMAIL
    if text == "📧 Авторизоваться по email":
        waiting_email[chat_id] = True
        send_msg(chat_id, "📧 Введи свой email:")
        return
    
    # EMAIL INPUT
    if chat_id in waiting_email:
        email = text.strip().lower()
        del waiting_email[chat_id]
        
        if not validate_email(email):
            send_msg(chat_id, "❌ Неправильный формат email!\nПопробуй снова /start")
            return
        
        if email_exists(email):
            send_msg(chat_id, "❌ Этот email уже зарегистрирован!\nПопробуй другой email или свяжись с поддержкой.")
            return
        
        if save_user_data(chat_id, email):
            send_msg(chat_id, f"✅ Авторизация успешна!\n📧 Email: {email}\nТеперь можешь генерировать изображения!", main_menu_keyboard())
        else:
            send_msg(chat_id, "❌ Ошибка при сохранении. Попробуй ещё раз.")
        return
    
    # MY ACCOUNT (Button)
    if text == "📧 Мой аккаунт":
        data = get_user_data(chat_id)
        count, limit = get_generation_count(chat_id)
        
        if data:
            send_msg(chat_id, f"👤 <b>Информация аккаунта:</b>\n📧 Email: {data['email']}\n📊 Сегодня: {count}/{limit}\n\nВыбери действие:", main_menu_keyboard())
        else:
            send_msg(chat_id, "❌ Не авторизован. Используй /start")
        return
    
    # GENERATE (Button)
    if text == "🎨 Генерировать":
        if not is_authorized(chat_id):
            return
        
        count, limit = get_generation_count(chat_id)
        if count >= limit:
            send_msg(chat_id, f"❌ Лимит достигнут! ({limit}/{limit})\nПопробуй завтра.")
            return
        
        if chat_id in waiting_prompt:
            return
        
        waiting_prompt[chat_id] = True
        send_msg(chat_id, f"🎨 Опиши изображение (сегодня: {count}/{limit}):")
        return
    
    # PROMPT INPUT
    if chat_id in waiting_prompt:
        prompt = text.strip()
        del waiting_prompt[chat_id]
        
        if len(prompt) < 3:
            send_msg(chat_id, "❌ Слишком короткое описание! Минимум 3 символа.")
            return
        
        count, limit = get_generation_count(chat_id)
        if count >= limit:
            send_msg(chat_id, f"❌ Лимит достигнут!")
            return
        
        send_msg(chat_id, f"⏳ Генерирую... (10-30 сек)\n📝 Запрос: {prompt[:50]}")
        img = gen_img(prompt)
        
        if img:
            try:
                Path("images").mkdir(exist_ok=True)
                fn = f"images/img_{chat_id}_{int(time.time())}.png"
                with open(fn, 'wb') as f:
                    f.write(img)
                
                increment_count(chat_id)
                new_count, limit = get_generation_count(chat_id)
                
                send_img(chat_id, fn, f"✨ <b>Готово!</b>\n📝 {prompt[:80]}\n📊 {new_count}/{limit}")
                send_msg(chat_id, "✅ Изображение отправлено! Что дальше?", main_menu_keyboard())
            except Exception as e:
                send_msg(chat_id, f"❌ Ошибка: {str(e)[:30]}")
        else:
            send_msg(chat_id, "❌ Ошибка генерации. Попробуй другое описание.")
        return
    
    # HELP (Button)
    if text == "ℹ️ Помощь":
        send_msg(chat_id, "🤖 <b>NeuroArtAI Bot</b>\n\n📸 Генерируй AI изображения\n📧 Один email = один аккаунт\n⏰ Лимит: 10 в день\n\n<b>Используй команды:</b>\n/start /profile /generate /help", main_menu_keyboard())
        return
    
    # DEFAULT
    send_msg(chat_id, "👆 Используй кнопки ниже!", main_menu_keyboard())

def main():
    """Main polling loop"""
    global processed
    offset = 0
    
    print("[POLLING] Starting polling loop...")
    
    while True:
        try:
            # Используем longer timeout для long polling
            r = requests.post(
                f"{API_URL}/getUpdates",
                json={"offset": offset, "timeout": 30},
                timeout=35
            )
            
            if r.status_code != 200:
                print(f"[ERROR] Telegram API error: {r.status_code}")
                time.sleep(2)
                continue
            
            updates = r.json().get("result", [])
            
            if not updates:
                # Нет новых сообщений, продолжаем опрос
                continue
            
            print(f"[UPDATES] Got {len(updates)} updates")
            
            for upd in updates:
                try:
                    offset = upd.get("update_id", 0) + 1
                    msg = upd.get("message", {})
                    
                    if not msg:
                        continue
                    
                    chat_id = msg.get("chat", {}).get("id")
                    text = msg.get("text", "").strip()
                    msg_id = msg.get("message_id")
                    
                    if not (chat_id and text and msg_id):
                        continue
                    
                    # Дедупликация
                    key = f"{chat_id}_{msg_id}"
                    if key in processed:
                        print(f"[SKIP] Duplicate message: {key}")
                        continue
                    
                    processed.add(key)
                    print(f"[MSG] Chat {chat_id}: {text[:50]}")
                    
                    # Обработай сообщение
                    handle(chat_id, text)
                    
                except Exception as e:
                    print(f"[ERROR] Processing update: {e}")
                    continue
        
        except requests.exceptions.Timeout:
            print("[TIMEOUT] Request timeout, retrying...")
            time.sleep(2)
        except requests.exceptions.ConnectionError:
            print("[ERROR] Connection error, retrying...")
            time.sleep(5)
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    setup_commands()
    main()

