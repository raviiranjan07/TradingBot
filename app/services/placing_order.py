def set_leverage(exchange, symbol="ETH/USDT", leverage=125):
    markets = exchange.load_markets()  # Load markets first
    market = exchange.market(symbol)   # Get market details
        
    exchange.fapiPrivate_post_leverage({
        'symbol': market['id'],       # e.g., 'ETHUSDT'
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

def place_order(exchange, symbol, side, qty):
    try:
        order = exchange.create_market_order(symbol=symbol, side=side, amount=qty)
        print(f"✅ {side.upper()} Order Placed | Qty: {qty}")
        return order
    except Exception as e:
        print(f"❌ Error placing order: {e}")
