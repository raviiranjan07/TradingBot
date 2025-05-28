import os
import requests

from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("tele_token")
chat_id = os.getenv("chat_id")

def telegram_msg(message: str):
    url = f"https://api.telegram.org/bot{api_key}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    return response.json()