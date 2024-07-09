import sys
from pathlib import Path
sys.path.append(str(Path('').resolve()))

from SETTINGS.settings__ import info_bmq
from keys import session
import numpy as np
from decimal import Decimal as D
from datetime import datetime
import time
from pprint import pprint

'''VALIDATE ↓
'''
def getSR(symbol, roundQty):
    klines = session.get_kline(symbol=symbol, category='linear', interval='60', limit=360)['result']['list']
    closes = np.unique(np.array([float(kline[4]) for kline in klines]))
    lowestGlobal = np.sort(closes)[::5]
    valuesGlobal = np.diff(lowestGlobal)
    valueMaxGlobal = np.round(np.max(valuesGlobal), roundQty[0])

    # SPLITTING VALUES
    split_indexGlobal = np.argmax(np.round(valuesGlobal, roundQty[0]) == valueMaxGlobal) + 1
    support_levelGlobal = np.round(np.mean(lowestGlobal[:split_indexGlobal]), roundQty[0])
    resistance_levelGlobal = np.round(np.mean(lowestGlobal[split_indexGlobal:]), roundQty[0])
    return support_levelGlobal, resistance_levelGlobal

def get_kline(symbol, interval, limit):
    return session.get_kline(symbol=symbol, category='linear', interval=interval, limit=limit)['result']['list']

def kline_check(kline_old, symbol, i):
    while True:
        print(f'Run #{i}')
        kline_new = get_kline(symbol=symbol, interval=1, limit=1)[0]
        time.sleep(0.3)
        if kline_old[0] != kline_new[0]:
            return get_kline(symbol=symbol, interval=1, limit=2)
        
def kline_verificate(symbol, side, round_qty, kline):
    s_global, r_global = getSR(symbol, round_qty)
    mark_price = get_last_price(symbol)
    s_mark_price = round(mark_price - ((mark_price / 100) * D(2)), round_qty[0])
    r_mark_price = round(mark_price + ((mark_price / 100) * D(2)), round_qty[0])
    kline_radius = D(kline[2]) - D(kline[3])
    close_open_radius = D(kline[4]) - D(kline[3])
    if side == 'Sell':
        ThresholdRadiusSell = round(kline_radius - (kline_radius * D(60 / 100)), round_qty[0])
        if (D(kline[1]) > D(kline[4])) and (close_open_radius < ThresholdRadiusSell) and s_mark_price > s_global and s_mark_price < r_global:
            return side
        else:
            with open(str(Path('').resolve().parent) + '\\SMQ_N\\signal.txt', 'w', encoding='utf-8') as f:
                f.write(f'BMQ: Ордер не прошел проверку.\n'
                        f'SGlobal: {s_global} ({s_mark_price > s_global})\n'
                        f'RGlobal: {r_global} ({r_mark_price < r_global})\n'
                        f'MarkPriceS: {s_mark_price}, MarkPriceR: {r_mark_price}, MarkPrice: {mark_price}\n'
                        f'KlinesOpen: {kline[1]}, KlinesClose: {kline[4]} ({D(kline[1]) > D(kline[4])})\n'
                        f'CloseOpenRadius: {close_open_radius}, ThresholdRadiusSell: {ThresholdRadiusSell} ({close_open_radius < ThresholdRadiusSell})\n'
                        f'Время - {datetime.now()}')
            return None
    else:
        ThresholdRadiusBuy = round(kline_radius - (kline_radius * D(40 / 100)), round_qty[0])
        if (D(kline[1]) < D(kline[4])) and (close_open_radius > ThresholdRadiusBuy) and r_mark_price < r_global and r_mark_price > s_global:
            return side
        else:
            with open(str(Path('').resolve().parent) + '\\SMQ_N\\signal.txt', 'w', encoding='utf-8') as f:
                f.write(f'BMQ: Ордер не прошел проверку.\n'
                        f'SGlobal: {s_global} ({s_mark_price > s_global})\n'
                        f'RGlobal: {r_global} ({r_mark_price < r_global})\n'
                        f'MarkPriceR: {r_mark_price}, MarkPriceS: {s_mark_price}, MarkPrice: {mark_price}\n'
                        f'KlinesOpen: {kline[1]}, KlinesClose: {kline[4]} ({D(kline[1]) < D(kline[4])})\n'
                        f'CloseOpenRadius: {close_open_radius}, ThresholdRadiusSell: {ThresholdRadiusBuy} ({close_open_radius > ThresholdRadiusBuy})\n'
                        f'Время - {datetime.now()}')
            return None

def kline_validate(symbol, side, roundQty, timeNow):
    klines = len(get_kline(symbol=symbol, interval=1, limit=240))
    klines1MinTime = get_kline(symbol=symbol, interval=1, limit=1)[0]
    klineCreateTime = int(klines1MinTime[0][:-3])

    if klines >= 240:
        if timeNow > klineCreateTime:
            klines1MinTime = kline_check(symbol=symbol, kline_old=klines1MinTime, i=1)[0]
        kline_check1 = kline_check(symbol=symbol, kline_old=klines1MinTime, i=2)[-1]
        print('Run completed^')
        
        # DEFINITION OF VALIDITY
        side = kline_verificate(
            symbol=symbol,
            side=side,
            kline=kline_check1,
            round_qty=roundQty
        ) 
        if side != None:
            return side

    else:
        with open(str(Path('').resolve().parent) + '\\SMQ_N\\signal.txt', 'w', encoding='utf-8') as f:
            f.write(f'BMQ: Ордер не прошел проверку.\n'
                    f'Klines: {klines}')
        return None

'''POSITION ↓
'''     
def get_balance():
    return D(session.get_wallet_balance(accountType=info_bmq['ACCOUNT_TYPE'].upper(), coin='USDT')['result']['list'][0]['coin'][0]['walletBalance'])
    
def get_last_price(symbol):
    return D(session.get_tickers(category='linear', symbol=symbol)['result']['list'][0]['lastPrice'])

def get_roundQty(symbol):
    data_minroundQty = session.get_instruments_info(category='linear', symbol=symbol)['result']['list'][0]['lotSizeFilter']['minOrderQty']
    data_minroundPrice = session.get_instruments_info(category='linear', symbol=symbol)['result']['list'][0]['priceFilter']['minPrice'].rstrip('0')
    tick_minround_price = session.get_instruments_info(category='linear', symbol=symbol)['result']['list'][0]['priceFilter']['tickSize'].rstrip('0')
    roundForQty = (len(data_minroundQty) - 2) if D(data_minroundQty) < 1 else 0
    roundForTPSL = (len(data_minroundPrice) - 2) if D(data_minroundPrice) < 1 else 0
    round_for_tpsl2 = (len(tick_minround_price) - 1) if D(tick_minround_price) < 1 else len(tick_minround_price)
    return roundForTPSL, roundForQty, round_for_tpsl2

'''MORE ↓
'''
def orders_distribution(orders):
    orders_limit = []
    for order in orders:
        if order['orderType'] == 'Limit':
            orders_limit.append(order)
    return orders_limit

if __name__ == '__main__':
    print('hello world! pluu')