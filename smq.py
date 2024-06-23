from pybit.unified_trading import HTTP
import time
from decimal import Decimal
from datetime import datetime

THRESHOLD_PERCENT = 3
LIMIT_PERCENT = 8
session = HTTP()

def fetch_data():
    data = session.get_tickers(category='linear')['result']['list']
    print(f'{datetime.now()}: Получил новые данные')
    return data

def smq():
    data_old = fetch_data()
    prices_old = {price['symbol']: Decimal(price['lastPrice']) for price in data_old}
    start_time = time.time()

    while True:
        # Проверка, прошла ли минута для обновления старых данных
        if time.time() - start_time >= 60:
            data_old = fetch_data()
            prices_old = {price['symbol']: Decimal(price['lastPrice']) for price in data_old}
            start_time = time.time()

        time.sleep(0.5)
        print(f'Check data. Time: {datetime.now()}')
        
        data_new = session.get_tickers(category='linear')['result']['list']
        for price_new in data_new:
            symbol = price_new['symbol']
            if symbol in prices_old:
                percent_change = round(((Decimal(price_new['lastPrice']) - prices_old[symbol]) / prices_old[symbol]) * 100, 2)
                if abs(percent_change) >= THRESHOLD_PERCENT and abs(percent_change) < LIMIT_PERCENT and 'USDT' in symbol:
                    with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
                        if percent_change < 0:
                            f.write(f'🔴Ticker: {symbol}\n'
                                    f'Percent: {percent_change}%')
                        if percent_change > 0:
                            f.write(f'🟢Ticker: {symbol}\n'
                                    f'Percent: {percent_change}%')
                    return symbol, percent_change