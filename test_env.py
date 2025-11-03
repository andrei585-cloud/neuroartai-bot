#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify bot setup"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("PROVERKA KONFIGURACIION TELEGRAM-BOTA")
print("=" * 60)

# Proveraem Python versiyu
print("\n[OK] Python version: " + sys.version.split()[0])

# Proveraem nalichie faylov
print("\n[CHECK] Fayly proekta:")
files_to_check = [".env", "bot.py", "requirements.txt", "Procfile", ".gitignore"]
for file in files_to_check:
    exists = "[OK]" if Path(file).exists() else "[NO]"
    print(f"  {exists} {file}")

# Proveraem peremennye okruzheniia
print("\n[CHECK] Peremennye okruzheniia:")
from dotenv import load_dotenv
load_dotenv()

telegram_token = os.getenv('TELEGRAM_TOKEN')
hf_token = os.getenv('HF_API_TOKEN')

if telegram_token:
    print(f"  [OK] TELEGRAM_TOKEN: {'*' * 10}...{telegram_token[-10:]}")
else:
    print("  [NO] TELEGRAM_TOKEN: NOT FOUND")

if hf_token:
    print(f"  [OK] HF_API_TOKEN: {'*' * 10}...{hf_token[-10:]}")
else:
    print("  [NO] HF_API_TOKEN: NOT FOUND")

# Proveraem zavisimosti
print("\n[CHECK] Zavisimosti:")
dependencies = {
    "telegram": "python-telegram-bot",
    "requests": "requests",
    "PIL": "Pillow",
    "dotenv": "python-dotenv"
}

all_ok = True
for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"  [OK] {name}")
    except ImportError:
        print(f"  [NO] {name} - NOT INSTALLED")
        all_ok = False

print("\n" + "=" * 60)
if all_ok and telegram_token and hf_token:
    print("[SUCCESS] SETUP COMPLETE! Bot is ready to run.")
else:
    print("[WARNING] Some issues found. Check configuration.")
print("=" * 60)

print("\n[INFO] Command to start bot:")
print("   python bot.py")
print("\n[INFO] Bot will wait for messages from Telegram.")
print("   Send /start to the bot to begin!")
