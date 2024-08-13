from session import *
from settings__ import files_content

import numpy as np
import asyncio

def g_last_prices():
    def s_unpacking_data(data):
        res = tuple(zip(*(
            (info['symbol'], float(info['lastPrice']))
            for info in data 
            if (
                'USDT' in info['symbol'] and 
                'USDC' not in info['symbol'] and 
                info['curPreListingPhase'] == ''
            )
        )))
        return np.array(res[0]), np.float64(res[1])
    
    return s_unpacking_data(
        np.array(session_.get_tickers(
            category='linear'
        )['result']['list'])
    )

def g_percent_change(symbols_old, prices_old):
    symbols_new, prices_new = g_last_prices()
    
    '''SET ⭣
    '''
    where = np.abs(prices_new / prices_old - 1)
    indeces = np.where(
        (where >= float(files_content['THRESHOLD_PERCENT'])) & 
        (where <= float(files_content['LIMIT_PERCENT']))
    )
    if np.size(indeces) > 0:
        symbol = symbols_new[indeces]
        if np.all(symbols_old[indeces] == symbol):
            return (
                next(iter(symbol)),
                next(iter(prices_new[indeces] / prices_old[indeces] - 1))
            )

async def g_round_qty(symbol):
    def sub(value):
        for index, el in enumerate(value):
            if el == '.':
                return len(value[index+1:])
        return 0
    
    instruments_info = session_.get_instruments_info(
        category='linear',
        symbol=symbol
    )['result']['list'][0]

    '''SET ⭣
    '''
    return tuple(map(lambda v: sub(v), (
        instruments_info['lotSizeFilter']['qtyStep'],
        instruments_info['priceFilter']['tickSize']
    )))

async def g_balance():
    return float(
        session.get_wallet_balance(
            accountType=files_content['ACCOUNT_TYPE'].upper(), 
            coin='USDT'
        )['result']['list'][0]['coin'][0]['availableToWithdraw']
    )

async def g_last_price(symbol):
    return float(
        session.get_tickers(
            category='linear', symbol=symbol
        )['result']['list'][0]['lastPrice']
    )

async def g_data(symbol):
    return await asyncio.gather(*tuple(map(asyncio.create_task, (
        g_round_qty(symbol),
        g_last_price(symbol),
        g_balance()
    ))))

async def g_positions():
    try:
        return session.get_positions(
            category='linear', 
            settleCoin='USDT'
        )['result']['list']
    except:
        pass

def g_side_validated(symbol, side, time):
    def s_kline_check(kline, i=None):
        nonlocal symbol
        while True:
            kline_ = session_.get_kline(symbol=symbol, interval=1, limit=1)['result']['list'][0]
            if kline[0] != kline_[0]:
                if not i:
                    return kline_
                return session_.get_kline(symbol=symbol, interval=1, limit=2)['result']['list'][-1]
    
    klines = session_.get_kline(symbol=symbol, interval=1, limit=240)['result']['list']
    
    '''SET ⭣
    '''
    if len(klines) >= 240:
        kline = klines[0]
        kline_time = kline[0]
        if time < int(kline_time):
            kline = s_kline_check(kline_time)
        for i in range(2):
            print('side_validate ⭢ next_kline')
            kline = s_kline_check(kline, i)
        kline = np.float32(kline)

        kline_4 = kline[4]
        kline_3 = kline[3]
        kline_radius = kline[2] - kline_3
        threshold_radius = kline_radius - (kline_radius * 0.5)
        close_radius = kline_4 - kline_3
        if_ = (
            kline_4 < kline[1],
            close_radius < threshold_radius
        )
        side_ = 'Sell' if all(if_) else None
        if all(not value for value in if_):
            side_ = 'Buy'
        if side == side_:
            print('side_validate ⭢ verified')
            return side
        print('side_validate ⭢ non verified')
        
if __name__ == '__main__':
    import time
    from pprint import pprint
    
    while True:
        start = time.time()
        percent_changes_old = g_last_prices()
        while time.time() - start < float(files_content['CYCLE_UPDATE']):
            res = g_percent_change(*percent_changes_old)
            print(res)
            break

