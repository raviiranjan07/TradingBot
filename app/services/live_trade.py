import websockets
import os
import json
import asyncio

from dotenv import load_dotenv
from binance.client import Client
from tabulate import tabulate
from colorama import Fore, Style



api_key = os.getenv('BINANCE_FUTURE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')

client = Client(api_key, secret_key)

positions_data = []
mark_prices = {}


def active_position():
    global position_data
    positions_data.clear() 

    # account_info = client.futures_account() ## calling: GET /api/v2/account
    account_info = client.futures_position_information() ## calling: GET /fapi/v2/positionRisk
    
    for pos in account_info:
        amt = float(pos['positionAmt'])
        if amt != 0.0:
            
            symbol = pos['symbol']
            entry_price = float(pos['entryPrice'])
            # leverage = int(pos['leverage'])
            liq_price = float(pos.get('liquidationPrice', 0))
            position_side = pos.get('positionSide', 'BOTH')
            
            positions_data.append ({
                "symbol": symbol,
                "positionAmt": amt,
                "entryPrice": entry_price,
                "positionSide": position_side,
                "liquidationPrice": liq_price,
                # "leverage": leverage
            })
    # print(json.dumps(positions_data, indent=1))
        
def get_ws_url():
    symbols = list(set([pos['symbol'].lower() for pos in positions_data]))
    streams = "/".join([f"{sym}@markPrice" for sym in symbols])
    return f"wss://fstream.binance.com/stream?streams={streams}"
        
def print_positions():
    os.system('cls' if os.name == 'nt' else 'clear')
    table = []
    
    for pos in positions_data:
        sym  = pos['symbol'].lower()
        mark = mark_prices.get(sym)
        if mark is None:
            continue
        
        entry = pos["entryPrice"]
        amt = pos["positionAmt"]
        side = pos["positionSide"]
        liq_price = float(pos.get('liquidationPrice', 0))
        
        if amt > 0:
            pnl = (mark - entry) * amt
            # pnl_percent = ((mark - entry) / entry) * 100
        else:
            pnl = (entry - mark) * abs(amt)
            # pnl_percent = ((entry - mark) / entry) * 100
            
        pnl_percentage = (pnl /(entry * abs(amt))) * 100
        
        # Color the PnL
        pnl_color = Fore.GREEN if pnl >= 0 else Fore.RED
        pnl_str = f"{pnl_color}{round(pnl, 2)}{Style.RESET_ALL}"
        percent_str = f"{pnl_color}{pnl_percentage:.2f}%{Style.RESET_ALL}"
            
        # Bold the mark price
        mark_price = f"{Fore.MAGENTA}\033[1m{round(mark, 2)}{Style.RESET_ALL}"
         
        # liq_warning = "💥" if (0 < liq_price < 2 * mark and abs(mark - liq_price) / mark < 0.02) else ""
        
        table.append([
            pos['symbol'], side, amt,
            round(entry, 2), mark_price,
            pnl_str,percent_str,liq_price,
            # liq_warning
        ])
    print(tabulate(table, headers=[
        "Symbol", "Side", "Amount", "Entry Price",
        "Mark Price", "USDT PnL", "PnL %", "Liq. Price",
        # "⚠"
    ], tablefmt="fancy_grid", colalign=("center",)*8))

async def track_mark_positions():
    active_position()
    ws_url = get_ws_url()
    
    async with websockets.connect(ws_url) as ws:
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            
            # stream = data['stream']
            payload = data['data']
            symbol = payload['s'].lower()
            mark_price = float(payload['p'])
            
            mark_prices[symbol] = mark_price
            print_positions()

def check_open_position(symbol, side):
    """
    Checks if there's already an open LONG or SHORT position for the given symbol.
    side: "buy" or "sell"
    """
    direction = "LONG" if side.lower() == "buy" else "SHORT"

    try:
        for pos in client.futures_position_information(symbol=symbol):
            if pos.get('positionSide') == direction:
                amt = float(pos['positionAmt'])
                return abs(amt) > 0
    except Exception as e:
        print(f"❌ Error checking position: {e}")
    
    return False


if __name__ == '__main__':
    try:
        asyncio.run(track_mark_positions())
    except KeyboardInterrupt:
        print("\nStopped tracking.")
        
    # active_position()
