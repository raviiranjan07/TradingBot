from .positions import check_open_position
from .state import eth_h
from .tele import telegram_msg

def set_leverage(exchange, symbol="ETH/USDT", leverage=125):
    markets = exchange.load_markets()  # Load markets first
    market = exchange.market(symbol)   # Get market details
        
    exchange.fapiPrivate_post_leverage({
        'symbol': market['id'],     
        'leverage': leverage
    })

def get_min_notional(exchange, symbol="ETH/USDT"):
    exchange.load_markets()
    market = exchange.market(symbol)

    filters = market['info']['filters']
    for f in filters:
        if f['filterType'] == 'MIN_NOTIONAL':
            return float(f['notional'])

    raise Exception("MIN_NOTIONAL filter not found")
    
def get_min_order_qty(price, exchange,leverage=125):
    min_notional = get_min_notional(exchange)
    margin = min_notional / leverage
    print(f"margin: {margin}")
    qty = min_notional / price
    return round(qty, 4)

def percentage_move():
    if eth_h.fixed_high >= 2.5:
            telegram_msg("📉 Gain ≥ 2.5% → Going SHORT (SELL)")
    if eth_h.fixed_low >= 2.5:
            telegram_msg("📈 Loss ≥ 2.5% → Going LONG (BUY)")  
    # if check_open_position("ETHUSDT","sell"):
    #     if eth_h.fixed_high >= 2.5:
    #         print("📉 Gain ≥ 2.5% → Going SHORT (SELL)")
    #         telegram_msg("📉 Gain ≥ 2.5% → Going SHORT (SELL)")
    #         qty = get_min_order_qty(eth_h.exchange, eth_h.current_price) 
    #         leveraged_value = qty * 125
    #         order_quantity  = leveraged_value/eth_h.current_price
            # print("🚫 Already in SHORT position. Skipping order.")
            # telegram_msg("🚫 Already in SHORT position. Skipping order.")
            
    # if check_open_position("ETHUSDT","buy"): 
    #     if eth_h.fixed_low >= 2.5:
    #         print("📈 Loss ≥ 2.5% → Going LONG (BUY)")    
    #         qty = get_min_order_qty(eth_h.exchange, eth_h.current_price) 
    #         leveraged_value = qty * 125
    #         order_quantity  = leveraged_value/eth_h.current_price
    #         # place_order(exchange, "ETH/USDT", "buy", qty)
    #         # await asyncio.sleep(5)

def place_order(exchange, symbol, side, qty):
    try:
        order = exchange.create_market_order(symbol=symbol, side=side, amount=qty)
        print(f"✅ {side.upper()} Order Placed | Qty: {qty}")
        return order
    except Exception as e:
        print(f"❌ Error placing order: {e}")
