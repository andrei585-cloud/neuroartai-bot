import requests
import os
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv('HF_API_TOKEN')
URL = 'https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0'

print("[TEST] Testing HF API...")
headers = {'Authorization': f'Bearer {HF_TOKEN}'}
try:
    r = requests.post(URL, headers=headers, json={'inputs': 'cat on beach'}, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

