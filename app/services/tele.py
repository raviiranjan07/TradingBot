# import os
# import requests

# from dotenv import load_dotenv

# load_dotenv()
# api_key = os.getenv("tele_token")
# chat_id = os.getenv("chat_id")

# def telegram_msg(message: str):
#     url = f"https://api.telegram.org/bot{api_key}/sendMessage"
#     payload = {
#         "chat_id": chat_id,
#         "text": message
#     }
#     response = requests.post(url, data=payload)
#     return response.json()

import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("tele_token")
chat_id = os.getenv("chat_id")

IP_LOG_FILE = "last_ip.txt"

def telegram_msg(message: str):
    url = f"https://api.telegram.org/bot{api_key}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return None

def get_current_ip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except Exception as e:
        print(f"❌ Error fetching IP: {e}")
        return None

def notify_ip_change(new_ip: str):
    message = (
        f"🆕 Server Started or IP Changed\n"
        f"🌐 Public IP: {new_ip}\n"
        f"⚠️ Update this IP in Binance API whitelist."
    )
    telegram_msg(message)

def check_ip_on_startup():
    current_ip = get_current_ip()
    telegram_msg(f"I.P : {current_ip}")
    
    if not current_ip:
        return

    if not os.path.exists(IP_LOG_FILE):
        with open(IP_LOG_FILE, "w") as f:
            f.write(current_ip)
        notify_ip_change(current_ip)
        return

    with open(IP_LOG_FILE, "r") as f:
        last_ip = f.read().strip()

    if current_ip != last_ip:
        notify_ip_change(current_ip)
        with open(IP_LOG_FILE, "w") as f:
            f.write(current_ip)
    else:
        telegram_msg(f"✅ IP unchanged: {current_ip}")