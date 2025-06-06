import os
import asyncio
import sys
import time
import ccxt
import json
import websockets
import time
from tabulate import tabulate

from dotenv import load_dotenv
from collections import deque

# from app.services.placing_order import get_min_order_qty
from app.services.positions import check_open_position 
from app.services.tele import telegram_msg
from app.services.state import eth_h 


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

price_window = deque()

TIME_WINDOW = 3600

TRADE_WS = "wss://fstream.binance.com/ws/ethusdt@trade"


async def kline_logic(exchange):
    # from app.services.order import percentage_move
    start_time = time.time()
    
    high = None
    low = None
    open= None
    fixed_high = 0
    fixed_low = 0
    
    eth_h.exchange = exchange
    
    try:
        async with websockets.connect(TRADE_WS) as ws:
            while True:
                # percentage_move()
                message = await ws.recv()
                data = json.loads(message)
                current_price = float(data['p'])
                now = time.time() 
                
                if open is None:
                    open = current_price
                    
                if now - start_time >= TIME_WINDOW:
                    print(f"\n--- Window ended. Resetting ---\n")
                    telegram_msg("🚦New window started")
                    start_time = now
                    high = 0
                    low = 0
                    open = current_price
                    fixed_high = 0
                    fixed_low = 0
                    
                if current_price == 0.0:
                    # print(f"⚠️ Warning: Received price = 0.0 at {time.strftime('%H:%M:%S', time.localtime(now))}")
                    continue
                
                if high and low and high != low:
                    percent_loss = ((high - low) / high) * 100 
                    percent_gain = ((high - low) / low) * 100 
                else:
                    percent_loss = percent_gain = 0
                
                def percentage_gain(high, low):
                    if low ==0:
                        return 0
                    else:
                        return ((high - low) / low) * 100

                def percentage_loss(high, low):
                    if low == 0:
                        return 0
                    else:
                        return ((high - low) / low) * 100
                                
                if current_price >= open and high != 0 and low!=0:
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
                
                output = (
                    f"{CYAN}Time elapsed: {formatted_elapsed}{RESET} | 🟢 Price: {current_price:.2f} | ⏰ open: {open}\n"
                    f"High: {high:.2f} | Low: {low:.2f} | {RED}F_Loss: {fixed_low:.2f}%{RESET} | {GREEN}F_Gain: {fixed_high:.2f}%{RESET} | {RED}Loss: {percent_loss:.2f}%{RESET} |"
                    f"{GREEN}Gain: {percent_gain:.2f}%{RESET}"
                )
                sys.stdout.write('\033[2J')   # Clear screen
                sys.stdout.write('\033[H')    # Move cursor to top-left (home position)
                sys.stdout.flush()

                print(output)
                                
                # ✅ Update shared state and trigger logic
                # eth_h.current_price = current_price
                # eth_h.fixed_high = fixed_high
                # eth_h.fixed_low = fixed_low

                # percentage_move()

    except websockets.ConnectionClosed as e:
        print(f"WebSocket connection closed with error: {e}. Reconnecting...")
        await asyncio.sleep(5)

# async def main():
#     # check_ip_on_startup()
#     exchange = create_binance_futures_client() 
    
#     # set_leverage(exchange, symbol="ETH/USDT", leverage=125) 
#     await asyncio.gather(kline_logic(exchange))

# if __name__ == "__main__":
#     asyncio.run(main())

