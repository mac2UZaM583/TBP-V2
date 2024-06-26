import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bmq_v2.keys import session
import numpy as np
from decimal import Decimal as D
from datetime import datetime
import time

'''VALIDATE ↓
'''
def getSR(symbol, roundQty):
    klines = session.get_kline(symbol=symbol, category='linear', interval='60', limit=360)['result']['list']
    closes = np.unique(np.array([float(kline[4]) for kline in klines]))
    lowestGlobal = np.sort(closes)[::5]
    lowestLocal = np.sort(closes)[:100:3]
    valuesGlobal = np.diff(lowestGlobal)
    valuesLocal = np.diff(lowestLocal)
    valueMaxGlobal = np.round(np.max(valuesGlobal), roundQty[0])
    valueMaxLocal = np.round(np.max(valuesLocal), roundQty[0])

    # SPLITTING VALUES
    split_indexGlobal = np.argmax(np.round(valuesGlobal, roundQty[0]) == valueMaxGlobal) + 1
    split_indexLocal = np.argmax(np.round(valuesLocal, roundQty[0]) == valueMaxLocal) + 1
    support_levelGlobal = np.round(np.mean(lowestGlobal[:split_indexGlobal]), roundQty[0])
    resistance_levelGlobal = np.round(np.mean(lowestGlobal[split_indexGlobal:]), roundQty[0])
    support_levelLocal = np.round(np.mean(lowestLocal[:split_indexLocal]), roundQty[0])
    resistance_levelLocal = np.round(np.mean(lowestLocal[split_indexLocal:]), roundQty[0])
    return support_levelGlobal, resistance_levelGlobal, support_levelLocal, resistance_levelLocal

def get_kline(symbol, interval, limit):
    return session.get_kline(symbol=symbol, category='linear', interval=interval, limit=limit)['result']['list']

def kline_check(kline_old, symbol, i):
    while True:
        print(f'Run #{i}')
        kline_new = get_kline(symbol=symbol, interval=1, limit=1)[0]
        time.sleep(0.3)
        if kline_old[0] != kline_new[0]:
            return get_kline(symbol=symbol, interval=1, limit=2)[-1]
        
def kline_verificate(side, kline, kline_radius, close_open_radius, s_global, s_local, r_global, r_local, s_mark_price, r_mark_price, mark_price, round_qty):
    if side == 'Sell':
        ThresholdRadiusSell = round(kline_radius - (kline_radius * D(60 / 100)), round_qty[0])
        if (D(kline[1]) > D(kline[4])) and (close_open_radius < ThresholdRadiusSell) and (s_mark_price > s_global or s_mark_price > s_local):
            return side
        else:
            print('ордер не прошел проверку21')
            with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
                f.write(f'BMQ: Ордер не прошел проверку.\n'
                        f'SGlobal: {s_global}, SLocal: {s_local}\n'
                        f'MarkPriceS: {s_mark_price}, MarkPrice: {mark_price}\n'
                        f'KlinesOpen: {kline[1]}, KlinesClose: {kline[4]}\n'
                        f'CloseOpenRadius: {close_open_radius}, ThresholdRadiusSell: {ThresholdRadiusSell}\n'
                        f'Время - {datetime.now()}')
            return None
    else:
        ThresholdRadiusBuy = round(kline_radius - (kline_radius * D(40 / 100)), round_qty[0])
        if (D(kline[1]) < D(kline[4])) and (close_open_radius > ThresholdRadiusBuy) and (r_mark_price < r_global or r_mark_price < r_local):
            return side
        else:
            print('ордер не прошел проверку22')
            with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
                f.write(f'BMQ: Ордер не прошел проверку.\n'
                        f'RGlobal: {r_global}, RLocal: {r_local}\n'
                        f'MarkPriceR: {r_mark_price}, MarkPrice: {mark_price}\n'
                        f'KlinesOpen: {kline[1]}, KlinesClose: {kline[4]}\n'
                        f'CloseOpenRadius: {close_open_radius}, ThresholdRadiusSell: {ThresholdRadiusBuy}\n'
                        f'Время - {datetime.now()}')
            return None

def kline_validate(symbol, side, roundQty, timeNow):
    klines = len(get_kline(symbol=symbol, interval=1, limit=240))
    klines1MinTime = get_kline(symbol=symbol, interval=1, limit=1)[0]
    klineCreateTime = int(klines1MinTime[0][:-3])
    
    if timeNow > klineCreateTime and klines >= 240:
        print(symbol)
        kline_check_none = kline_check(symbol=symbol, kline_old=klines1MinTime, i=1)
        kline_check1 = kline_check(symbol=symbol, kline_old=kline_check_none, i=2)
        print('Run completed^')
        
        # DEFINITION OF VALIDITY
        SGlobal, RGlobal, SLocal, RLocal = getSR(symbol, roundQty)
        markPrice = get_last_price(symbol)
        markPriceS = round(markPrice - ((markPrice / 100) * D(1.5)), roundQty[0])
        markPriceR = round(markPrice + ((markPrice / 100) * D(1.5)), roundQty[0])
        klineRadius = D(kline_check1[2]) - D(kline_check1[3])
        CloseOpenRadius = D(kline_check1[4]) - D(kline_check1[3])
        kline_verificate(side=side, kline=kline_check1, kline_radius=klineRadius, close_open_radius=CloseOpenRadius, s_global=SGlobal, s_local=SLocal, 
                         r_global=RGlobal, r_local=RLocal, s_mark_price=markPriceS, r_mark_price=markPriceR, mark_price=markPrice, round_qty=roundQty)
    else:
        print('ордер не прошел проверку1')
        with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
            f.write(f'BMQ: Ордер не прошел проверку.\n'
                    f'Время клайна - {klineCreateTime}\n'
                    f'Время записи - {timeNow}\n'
                    f'Klines: {klines}')
        return None

'''POSITION ↓
'''
def get_balance():
    return D(session.get_wallet_balance(accountType='UNIFIED', coin='USDT')['result']['list'][0]['coin'][0]['walletBalance'])
    
def get_last_price(symbol):
    return D(session.get_tickers(category='linear', symbol=symbol)['result']['list'][0]['lastPrice'])

def get_roundQty(symbol):
    data_minroundQty = session.get_instruments_info(category='linear', symbol=symbol)['result']['list'][0]['lotSizeFilter']['minOrderQty']
    data_minroundPrice = session.get_instruments_info(category='linear', symbol=symbol)['result']['list'][0]['priceFilter']['minPrice']
    roundForQty = (len(data_minroundQty) - 2) if D(data_minroundQty) < 1 else 0
    roundForTPSL = (len(data_minroundPrice) - 2) if D(data_minroundPrice) < 1 else len(data_minroundPrice)
    return roundForTPSL, roundForQty

def get_avg_position_price():
    return D(session.get_positions(category='linear', settleCoin='USDT')['result']['list'][-1]['avgPrice'])

'''MORE ↓
'''
def orders_distribution(orders):
    orders_limit = []
    orders_tp = []
    orders_sl = []
    for order in orders:
        if order['orderType'] == 'Limit':
            orders_limit.append(order)
        if order['createType'] == 'CreateByTakeProfit':
            orders_tp.append(order)
        if order['createType'] == 'CreateByTakeProfit':
            orders_sl.append(order)
    return orders_limit, orders_tp, orders_sl