from pybit.unified_trading import HTTP
import time
from decimal import Decimal
from multiprocessing import Process, Queue

THRESHOLD_PERCENT = 3
session = HTTP()

def get_tickers():
    info = session.get_tickers(category='linear')['result']['list']
    return [ticker['symbol'] for ticker in info if 'USDC' not in ticker['symbol'] and 'USDT' in ticker['symbol']]

def scrcr1(queue):
    while True:
        print('я бог криптовалюты и я анализирую рынок. попытка номер плю1')
        data_old = session.get_tickers(category='linear')['result']['list']
        pricesOld = []
        for price in data_old:
            pricesOld.append(Decimal(price['lastPrice']))
        time.sleep(60)

        data_new = session.get_tickers(category='linear')['result']['list']
        for priceOld, priceNew in zip(data_old, data_new):
            percent_change = round(((Decimal(priceNew['lastPrice']) - Decimal(priceOld['lastPrice'])) / Decimal(priceOld['lastPrice'])) * 100, 2)
            if abs(percent_change) >= THRESHOLD_PERCENT:
                queue.put((priceNew['symbol'], percent_change))

def scrcr2(queue):
    while True:
        print('я 2 бог криптовалюты и я анализирую рынок. попытка номер плю2')
        data_old = session.get_tickers(category='linear')['result']['list']
        pricesOld = []
        for price in data_old:
            pricesOld.append(Decimal(price['lastPrice']))
        time.sleep(20)

        data_new = session.get_tickers(category='linear')['result']['list']
        for priceOld, priceNew in zip(data_old, data_new):
            percent_change = round(((Decimal(priceNew['lastPrice']) - Decimal(priceOld['lastPrice'])) / Decimal(priceOld['lastPrice'])) * 100, 2)
            if abs(percent_change) >= THRESHOLD_PERCENT:
                queue.put((priceNew['symbol'], percent_change))

def scrcr3(queue):
    while True:
        print('я 3 бог криптовалюты и я анализирую рынок. попытка номер плю3')
        data_old = session.get_tickers(category='linear')['result']['list']
        pricesOld = []
        for price in data_old:
            pricesOld.append(Decimal(price['lastPrice']))
        time.sleep(5)

        data_new = session.get_tickers(category='linear')['result']['list']
        for priceOld, priceNew in zip(data_old, data_new):
            percent_change = round(((Decimal(priceNew['lastPrice']) - Decimal(priceOld['lastPrice'])) / Decimal(priceOld['lastPrice'])) * 100, 2)
            if abs(percent_change) >= THRESHOLD_PERCENT:
                queue.put((priceNew['symbol'], percent_change))

def scrcr4(queue):
    while True:
        print('я 4 бог криптовалюты и я анализирую рынок. попытка номер плю4')
        data_old = session.get_tickers(category='linear')['result']['list']
        pricesOld = []
        for price in data_old:
            pricesOld.append(Decimal(price['lastPrice']))
        time.sleep(2)

        data_new = session.get_tickers(category='linear')['result']['list']
        for priceOld, priceNew in zip(data_old, data_new):
            percent_change = round(((Decimal(priceNew['lastPrice']) - Decimal(priceOld['lastPrice'])) / Decimal(priceOld['lastPrice'])) * 100, 2)
            if abs(percent_change) >= THRESHOLD_PERCENT:
                queue.put((priceNew['symbol'], percent_change))
            
def smq():
    queue = Queue()
    process1 = Process(target=scrcr1, args=(queue,))
    process2 = Process(target=scrcr2, args=(queue,))
    process3 = Process(target=scrcr3, args=(queue,))
    process4 = Process(target=scrcr4, args=(queue,))
    process1.start()
    process2.start()
    process3.start()
    process4.start()

    result = queue.get()
    if result is not None:
        with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
            if result[1] < 0:
                f.write(f'🔴Ticker: {result[0]}\n'
                        f'Percent - {result[1]}%')
            if result[1] > 0:
                f.write(f'🟢Ticker: {result[0]}\n'
                        f'Percent - {result[1]}%')  
        return result

    process1.join()
    process2.join()
    process3.join()
    process4.join()

# if __name__ == '__main__':
#     while True:
#         signal = smq()
#         print(signal)