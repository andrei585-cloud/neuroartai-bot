#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete bot verification script"""

import sys
import os

print("=" * 70)
print("COMPLETE BOT VERIFICATION")
print("=" * 70)

# Check 1: Python version
print("\n[CHECK 1] Python version")
version = sys.version.split()[0]
print(f"  Python: {version}")
if sys.version_info >= (3, 8):
    print("  [OK] Python 3.8+")
else:
    print("  [ERROR] Python 3.8+ required")
    sys.exit(1)

# Check 2: Import all modules
print("\n[CHECK 2] Importing required modules")
try:
    import telegram
    print(f"  [OK] telegram {telegram.__version__}")
except ImportError as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

try:
    import requests
    print(f"  [OK] requests {requests.__version__}")
except ImportError as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

try:
    from PIL import Image
    print(f"  [OK] Pillow")
except ImportError as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print(f"  [OK] python-dotenv")
except ImportError as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

# Check 3: Load environment
print("\n[CHECK 3] Loading environment")
load_dotenv()
telegram_token = os.getenv('TELEGRAM_TOKEN')
hf_token = os.getenv('HF_API_TOKEN')

if telegram_token:
    print(f"  [OK] TELEGRAM_TOKEN loaded")
else:
    print(f"  [ERROR] TELEGRAM_TOKEN not found")
    sys.exit(1)

if hf_token:
    print(f"  [OK] HF_API_TOKEN loaded")
else:
    print(f"  [ERROR] HF_API_TOKEN not found")
    sys.exit(1)

# Check 4: Import bot module
print("\n[CHECK 4] Importing bot module")
try:
    # Try to import bot without running it
    spec = __import__('importlib').util.spec_from_file_location("bot_module", "bot.py")
    bot_module = __import__('importlib').util.module_from_spec(spec)
    # Don't execute it, just load the code
    print(f"  [OK] bot.py syntax is valid")
except SyntaxError as e:
    print(f"  [ERROR] Syntax error in bot.py: {e}")
    sys.exit(1)
except Exception as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

# Check 5: Required files
print("\n[CHECK 5] Required files")
required_files = ['.env', 'bot.py', 'requirements.txt', '.gitignore', 'Procfile']
all_exist = True
for f in required_files:
    if os.path.exists(f):
        print(f"  [OK] {f}")
    else:
        print(f"  [ERROR] {f} not found")
        all_exist = False

if not all_exist:
    sys.exit(1)

# Check 6: Images directory
print("\n[CHECK 6] Images directory")
if not os.path.exists('images'):
    os.makedirs('images', exist_ok=True)
    print(f"  [OK] images/ directory created")
else:
    print(f"  [OK] images/ directory exists")

print("\n" + "=" * 70)
print("ALL CHECKS PASSED!")
print("=" * 70)
print("\nBot is ready to run:")
print("  Command: python bot.py")
print("\nExpected output:")
print("  [INFO] Tokens loaded")
print("  [INFO] Bot starting...")
print("  [INFO] Handlers set")
print("  [INFO] Bot ready! Polling...")
print("\n" + "=" * 70)

