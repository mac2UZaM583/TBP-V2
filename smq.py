from pybit.unified_trading import HTTP
import time
from decimal import Decimal

THRESHOLD_PERCENT = 3.0
session = HTTP()

def get_tickers():
    info = session.get_tickers(category='linear')['result']['list']
    return [ticker['symbol'] for ticker in info if 'USDC' not in ticker['symbol'] and 'USDT' in ticker['symbol']]

def smq():
    while True:
        print('я бог криптовалюты и я анализирую рынок. попытка номер плю')
        data_old = session.get_tickers(category='linear')['result']['list']
        pricesOld = []
        for price in data_old:
            pricesOld.append(Decimal(price['lastPrice']))
        time.sleep(7)

        data_new = session.get_tickers(category='linear')['result']['list']
        for priceOld, priceNew in zip(data_old, data_new):
            percent_change = round(((Decimal(priceNew['lastPrice']) - Decimal(priceOld['lastPrice'])) / Decimal(priceOld['lastPrice'])) * 100, 2)
            if percent_change >= THRESHOLD_PERCENT:
                # print(f'{priceNew['symbol']} | {percent_change}%')
                return priceNew['symbol'], percent_change