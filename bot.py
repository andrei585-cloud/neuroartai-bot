#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    print("[FATAL] Переменная TELEGRAM_TOKEN не задана. Установите её в Railway Variables или локально в окружении.")
    raise SystemExit(1)

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
OFFSET_FILE = "offset.txt"

print("[STARTUP] Бот запущен")


def load_offset():
    """Загрузка последнего offset с диска"""
    if os.path.exists(OFFSET_FILE):
        try:
            with open(OFFSET_FILE, "r", encoding="utf-8") as f:
                raw = f.read().strip()
                return int(raw) if raw.isdigit() else 0
        except Exception:
            return 0
    return 0


def save_offset(offset: int) -> None:
    """Сохранение offset на диск"""
    try:
        with open(OFFSET_FILE, "w", encoding="utf-8") as f:
            f.write(str(offset))
    except Exception:
        pass


def setup_commands() -> None:
    """Регистрирует команды в меню Telegram (локализация RU)."""
    try:
        cmds = [
            {"command": "start", "description": "Запуск бота"},
            {"command": "help", "description": "Как пользоваться"},
        ]
        # Устанавливаем команды для русского языка
        requests.post(
            f"{API_URL}/setMyCommands",
            json={"commands": cmds, "language_code": "ru"},
            timeout=10,
        )
    except Exception:
        pass


def disable_webhook() -> None:
    """Гарантированно отключает webhook, чтобы избежать 409-конфликта с getUpdates."""
    try:
        # Если был установлен webhook, отключим его (не сбрасывая очереди сообщений)
        requests.post(
            f"{API_URL}/deleteWebhook",
            json={"drop_pending_updates": False},
            timeout=10,
        )
    except Exception:
        pass


def send_msg(chat_id: int, text: str) -> None:
    try:
        requests.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
    except Exception:
        pass


def send_photo(chat_id: int, image_path: str, caption: str) -> None:
    try:
        with open(image_path, "rb") as f:
            requests.post(
                f"{API_URL}/sendPhoto",
                files={"photo": f},
                data={"chat_id": chat_id, "caption": caption},
                timeout=60,
            )
    except Exception:
        pass


def gen_img(prompt: str) -> bytes | None:
    """Получает изображение от Pollinations по текстовому запросу."""
    try:
        import urllib.parse

        safe_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}"
        r = requests.get(url, timeout=60, allow_redirects=True)
        if r.status_code == 200 and r.content and len(r.content) > 1000:
            return r.content
    except Exception:
        return None
    return None


def main() -> None:
    # Отключаем webhook, чтобы не было конфликта с long-polling
    disable_webhook()
    setup_commands()
    offset = load_offset()
    print(f"[LOAD] Стартуем с offset={offset}")

    while True:
        try:
            resp = requests.post(
                f"{API_URL}/getUpdates",
                json={"offset": offset, "timeout": 30},
                timeout=35,
            )
            if resp.status_code != 200:
                print(f"[POLL ERROR] HTTP {resp.status_code}")
                time.sleep(1)
                continue

            updates = resp.json().get("result", [])
            if not updates:
                time.sleep(0.5)
                continue

            for upd in updates:
                update_id = upd.get("update_id", 0)
                msg = upd.get("message") or {}
                chat_id = (msg.get("chat") or {}).get("id")
                text = (msg.get("text") or "").strip()

                if not chat_id:
                    offset = update_id + 1
                    save_offset(offset)
                    continue

                t = text.lower()

                # Русские алиасы команд
                if t in ("/start", "start", "/старт", "старт"):
                    send_msg(
                        chat_id,
                        "Привет! Пришли мне описание картинки, и я сгенерирую изображение 🎨",
                    )
                elif t in ("/help", "help", "/помощь", "помощь"):
                    send_msg(
                        chat_id,
                        "Как пользоваться: просто отправьте текстовое описание изображения. Я отвечу картинкой.",
                    )
                elif t.startswith("/"):
                    # Неизвестная команда на любом языке — подскажем, что делать
                    send_msg(chat_id, "Пришлите обычный текст — я сгенерирую изображение.")
                elif text:
                    # Любой текст → генерация
                    print(f"[GEN] prompt='{text[:60]}'")
                    send_msg(chat_id, f"⏳ Генерирую... ({text[:60]})")
                    img = gen_img(text)
                    if img:
                        Path("images").mkdir(parents=True, exist_ok=True)
                        fn = f"images/img_{chat_id}_{int(time.time())}.png"
                        with open(fn, "wb") as f:
                            f.write(img)
                        send_photo(chat_id, fn, f"Готово: {text[:100]}")
                    else:
                        send_msg(chat_id, "❌ Не удалось сгенерировать. Попробуйте ещё раз.")

                # Обновляем offset ПОСЛЕ обработки
                offset = update_id + 1
                save_offset(offset)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()

