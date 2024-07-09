import sys
from pathlib import Path
sys.path.append(str(Path('').resolve().parent))
from pprint import pprint
pprint(__file__)
pprint(sys.path)

from SETTINGS.settings__ import (
    info_bmq,
    info_smq
)
from BMQ_V2.smq import smq, fetch_data
from BMQ_V2.get import (
    get_balance as gb, 
    get_roundQty as gr, 
    get_last_price as gl, 
    kline_validate as kV, 
    orders_distribution as od,
)
from BMQ_V2.set import (
    switch_margin_mode as smm, 
    place_orders_limit as pol, 
    place_order as po, 
    TP,
    SL,
    cancel_position
)
from BMQ_V2.keys import session
from decimal import Decimal as D
import time
import traceback

print(f'\n\nSTART-V2\n\n')
tp = []
for k, v in info_bmq.items():
    if 'TAKEPROFIT' in k:
        tp.append(D(v))
sl = D(info_bmq['STOPLOSS'])
limit_percent_price = D(info_bmq['LIMIT_PERCENT_PRICE'])

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

        if time.time() - start_time >= D(info_smq['DATA_UPDATE']):
            data_old = fetch_data()
            prices_old = {price['symbol']: D(price['lastPrice']) for price in data_old}
            start_time = time.time()
        signal = smq(prices_old=prices_old)
        if signal != None:
            return signal, positions

'''POST ↓
'''
def pre_main2(signal, positions):
    timeNow = int(time.time())
    balanceWL = gb()
    roundQty =  gr(signal[0])
    if not positions:
        session.cancel_all_orders(category="linear", settleCoin='USDT')
        side = kV(symbol=signal[0], side=signal[1], roundQty=roundQty, timeNow=timeNow)
        if side != None:
            smm(symbol=signal[0])
            mark_price = gl(signal[0])
            qty = round(balanceWL / mark_price, roundQty[1])
            po(symbol=signal[0], side=side, qty=qty)   
            pol(symbol=signal[0], side=side, qty=qty, round_qty=roundQty, percent_price=limit_percent_price)

def main():
    while True:
        try:
            '''PRE ↓
            '''
            signal, positions = pre_main1()
            
            '''POST ↓
            '''
            pre_main2(signal=signal, positions=positions)
        except:
            cancel_position()
            er = traceback.format_exc()
            with open(str(Path('').resolve().parent) + '\\SMQ_N\\signal.txt', 'w', encoding='utf-8') as f:
                f.write(f'{er}\n\ntime: {time.time()}')

if __name__ == '__main__':
    main()