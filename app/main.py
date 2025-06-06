import uvicorn
import os
import asyncio
from fastapi import FastAPI
from .services.tele import telegram_msg
from app.services.eth_1h import kline_logic, create_binance_futures_client

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    telegram_msg("🚩 BOT STARTED")
    exchange = create_binance_futures_client()
    
    await asyncio.create_task(kline_logic(exchange))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
