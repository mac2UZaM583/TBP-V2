import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from smq import smq, fetch_data
from bmq_v2.keys import session
from bmq_v2.read import (
    get_balance as gb, 
    get_roundQty as gr, 
    get_last_price as gl, 
    kline_validate as kV, 
    orders_distribution as od
)
from bmq_v2.write import (
    switch_margin_mode as smm, 
    place_order_limit as pol, 
    place_order as po, 
    TP,
    SL
)
from decimal import Decimal as D
import time
import traceback

print(f'\n\nSTART\n\n')
tp = [D(0.012), D(0.007), D(0.0048), D(0.0036), D(0.003)]
sl = D(0.070)

'''PRE ↓
'''
def pre_main1():
    data_old = fetch_data()
    prices_old = {price['symbol']: D(price['lastPrice']) for price in data_old}
    start_time = time.time()
    while True:
        positions = session.get_positions(category='linear', settleCoin='USDT')['result']['list']
        if positions:
            orders_limit = od(session.get_open_orders(category='linear', settleCoin='USDT')['result']['list'])
            TP(position=positions[-1], orders_limit_num=len(orders_limit), tp=tp)
            SL(position=positions[-1], orders_limit=orders_limit, sl=sl)
        else:
            session.cancel_all_orders(category='linear', settleCoin='USDT')

        if time.time() - start_time >= 60:
            data_old = fetch_data()
            prices_old = {price['symbol']: D(price['lastPrice']) for price in data_old}
            start_time = time.time()
        signal = smq(prices_old=prices_old)
        if signal != None:
            return signal, positions

'''POST ↓
'''
def ppre_main1(signal, side, qty, roundQty):
    avg_position_price = D(session.get_positions(category='linear', settleCoin='USDT')['result']['list'][-1]['avgPrice'])
    radius_price = avg_position_price * D(0.03)
    for i in range(1, 5):
        price = round(avg_position_price + (radius_price * (i if side == 'Sell' else -i)), roundQty[0])
        pol(symbol=signal[0], side=side, qty=qty, price=price, i=i+1)
    return avg_position_price, radius_price

'''PRE/POSITION ↓
'''
def pre_main2(signal, positions):
    timeNow = int(time.time())
    balanceWL = gb()
    roundQty =  gr(signal[0])
    if not positions:
        session.cancel_all_orders(category="linear", settleCoin='USDT')
        side = kV(symbol=signal[0], side='Buy' if signal[1] < 0 else 'Sell', roundQty=roundQty, timeNow=timeNow)
        if side != None:
            smm(symbol=signal[0])
            mark_price = gl(signal[0])
            qty = round(balanceWL / mark_price, roundQty[1])
            po(symbol=signal[0], side=side, qty=qty)   
            ppre_main1(signal=signal, side=side, qty=qty, roundQty=roundQty)

def main():
    while True:
        try:
            '''PRE POSITION ↓
            '''
            signal, positions = pre_main1()
            
            '''POSITION ↓
            '''
            pre_main2(signal=signal, positions=positions)
        except Exception:
            traceback.print_exc()

if __name__ == '__main__':
    main()