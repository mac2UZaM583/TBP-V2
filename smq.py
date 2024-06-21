from pybit.unified_trading import HTTP
import time
from decimal import Decimal
from datetime import datetime
from multiprocessing import Process, Queue

THRESHOLD_PERCENT = 3
session = HTTP()

def fetch_data(dataQueue):
    while True:
        data = session.get_tickers(category='linear')['result']['list']
        print('получил новые данные')        
        dataQueue.put(data)
        time.sleep(60)

def process_data(dataQueue, result_queue):
    while True:
        data_old = dataQueue.get()
        prices_old = {price['symbol']: Decimal(price['lastPrice']) for price in data_old}
        while True:
            time.sleep(1)
            print(f'Check data. Time: {datetime.now()}')
            
            data_new = session.get_tickers(category='linear')['result']['list']
            for price_new in data_new:
                symbol = price_new['symbol']
                if symbol in prices_old:
                    percent_change = round(((Decimal(price_new['lastPrice']) - prices_old[symbol]) / prices_old[symbol]) * 100, 2)
                    if abs(percent_change) >= THRESHOLD_PERCENT and 'USDT' in symbol:
                        result_queue.put((symbol, percent_change))
            
def smq():
    dataQueue = Queue()
    result_queue = Queue()
    Process(target=fetch_data, args=(dataQueue,)).start()
    Process(target=process_data, args=(dataQueue, result_queue)).start()

    while True:
        result = result_queue.get()
        if result is not None:
            with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
                if result[1] < 0:
                    f.write(f'🔴Ticker: {result[0]}\n'
                            f'Percent - {result[1]}%')
                if result[1] > 0:
                    f.write(f'🟢Ticker: {result[0]}\n'
                            f'Percent - {result[1]}%')
            return result

# if __name__ == '__main__':
#     while True:
#         signal = smq()
#         print(signal)