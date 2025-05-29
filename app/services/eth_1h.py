import os
import asyncio
import sys
import ccxt
import time
import json
import websockets
import logging

# import pandas as pd
# import pandas_ta as ta

from dotenv import load_dotenv
from collections import deque

# from app.services.placing_order import get_min_order_qty, place_order, set_leverage
from app.services.live_trade import check_open_position
from app.services.tele import telegram_msg


load_dotenv()

api_key = os.getenv('BINANCE_FUTURE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')


def create_binance_futures_client():
    return ccxt.binance({
        'apiKey': api_key,
        'secret': secret_key,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',  
        },
    })

# candle_window = deque(maxlen=60)
price_window = deque()

TIME_WINDOW = 3600

TRADE_WS = "wss://fstream.binance.com/ws/ethusdt@trade"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)

async def kline_logic(exchange):
    start_time = time.time()
    
    high = None
    low = None
    open= None
    fixed_high = 0
    fixed_low = 0
    
    try:
        async with websockets.connect(TRADE_WS) as ws:
            while True:
                message = await ws.recv()
                data = json.loads(message)
                current_price = float(data['p'])
                now = time.time() 
                
                if open is None:
                    open = current_price
                    
                if now - start_time >= TIME_WINDOW:
                    print(f"\n--- Window ended. Resetting ---\n")
                    start_time = now
                    high = 0
                    low = 0
                    open = 0
                    fixed_high = 0
                    fixed_low = 0
                    
                if current_price == 0.0:
                    # print(f"⚠️ Warning: Received price = 0.0 at {time.strftime('%H:%M:%S', time.localtime(now))}")
                    continue
                # # Calculate real-time % loss and gain based on current high/low
                if high and low and high != low:
                    percent_loss = ((high - low) / high) * 100 
                    percent_gain = ((high - low) / low) * 100 
                else:
                    percent_loss = percent_gain = 0
                
                def percentage_gain(high, low):
                    return ((high - low) / low) * 100
                def percentage_loss(high,low):
                    return ((high - low) / low) * 100 
                
                if current_price >= open:
                    high = current_price
                    low = open
                
                    fixed_high = max(fixed_high,percentage_gain(high,low))
                    if current_price < high and current_price > low:
                        high = current_price
                        fixed_low = max(fixed_low, percentage_loss(high, low))
                        if current_price < low:
                            low = current_price
                            fixed_low = max(fixed_low,percentage_loss(high, low))
                            
                elif current_price < open:
                    high = open
                    low = current_price
                    
                    fixed_low = max(fixed_low, percentage_loss(high, low))
                    if current_price > low and current_price < high:
                        low = current_price
                        fixed_high = max(fixed_high, percentage_gain(high, low))
                        if current_price > high:
                            high = current_price
                            fixed_high = max(fixed_high,percentage_gain(high,low))

                        
                elapsed = int(now - start_time)
                formatted_elapsed = time.strftime('%H:%M:%S', time.gmtime(elapsed))
                
                # ANSI color codes
                RESET = "\033[0m"
                BOLD = "\033[1m"
                GREEN = "\033[92m"
                RED = "\033[91m"
                YELLOW = "\033[93m"
                CYAN = "\033[96m"
                MAGENTA = "\033[95m"
                
                # output = (
                #     f"{CYAN}Time elapsed: {formatted_elapsed}{RESET} | 🟢 Price: {current_price:.2f} | ⏰ open: {open}\n"
                #     f"High: {high:.2f} | Low: {low:.2f} | {RED}F_Loss: {fixed_low:.2f}%{RESET} | {GREEN}F_Gain: {fixed_high:.2f}%{RESET} | {RED}Loss: {percent_loss:.2f}%{RESET} |"
                #     f"{GREEN}Gain: {percent_gain:.2f}%{RESET}"
                # )

                # # Move up 2 lines and clear
                # sys.stdout.write('\033[F\033[K\033[F\033[K')
                # print(output, end='')

                output = (
                    f"Time elapsed: {formatted_elapsed} | 🟢 Price: {current_price:.2f} | ⏰ open: {open:.2f}\n"
                    f"High: {high:.2f} | Low: {low:.2f} | "
                    f"F_Loss: {fixed_low:.2f}% | F_Gain: {fixed_high:.2f}% | "
                    f"Loss: {percent_loss:.2f}% | Gain: {percent_gain:.2f}%"
                )

                logging.info(output)
                
                if fixed_high >= 2.5:
                    print("📉 Gain ≥ 2.5% → Going SHORT (SELL)")
                    telegram_msg("📉 Gain ≥ 2.5% → Going SHORT (SELL)")
                    if check_open_position("ETHUSDT","sell"):
                        print("🚫 Already in SHORT position. Skipping order.")
                        telegram_msg("🚫 Already in SHORT position. Skipping order.")
                    else:
                        # qty = get_min_order_qty(exchange, current_price)
                        # place_order(exchange, "ETH/USDT", "sell", qty)
                        # await asyncio.sleep(5)  # small delay to avoid spamming orders
                        pass
                elif fixed_low >= 2.5:
                    print("📈 Loss ≥ 2.5% → Going LONG (BUY)")
                    telegram_msg("📈 Loss ≥ 2.5% → Going LONG (BUY)")
                    if check_open_position("ETHUSDT","buy"):
                        print("🚫 Already in LONG position. Skipping order.")
                        telegram_msg("🚫 Already in LONG position. Skipping order.")
                    else:
                        # place_order(exchange, "ETH/USDT", "buy", qty)
                        # await asyncio.sleep(5)
                        pass

    except websockets.ConnectionClosed as e:
        print(f"WebSocket connection closed with error: {e}. Reconnecting...")
        await asyncio.sleep(5)

    
async def main():
    exchange = create_binance_futures_client()
    # set_leverage(exchange, symbol="ETH/USDT", leverage=125) 
    await asyncio.gather(kline_logic(exchange))
    

if __name__ == "__main__":
    asyncio.run(main())