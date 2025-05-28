import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("tele_token")

url = f"https://api.telegram.org/bot{api_key}/getUpdates"

response = requests.get(url)
data = response.json()

print(data)  # This shows all recent messages to your bot

# Extract chat_id from the first message (assuming only one message)
if data["result"]:
    chat_id = data["result"][0]["message"]["chat"]["id"]
    print("Your chat ID is:", chat_id)
else:
    print("No messages found.")