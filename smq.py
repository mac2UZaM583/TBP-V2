from pybit.unified_trading import HTTP
import time
from decimal import Decimal
from multiprocessing import Process, Queue, current_process

THRESHOLD_PERCENT = 3
session = HTTP()

def fetch_data(queue):
    while True:
        data = session.get_tickers(category='linear')['result']['list']
        queue.put(data)
        time.sleep(5)

def process_data(queue, result_queue, interval):
    while True:
        process_name = current_process().name
        print(f'{process_name} анализирует рынок.')
        
        data_old = queue.get()
        prices_old = {price['symbol']: Decimal(price['lastPrice']) for price in data_old}
        time.sleep(interval)
        
        data_new = queue.get()
        for price_new in data_new:
            symbol = price_new['symbol']
            if symbol in prices_old:
                percent_change = round(((Decimal(price_new['lastPrice']) - prices_old[symbol]) / prices_old[symbol]) * 100, 2)
                if abs(percent_change) >= THRESHOLD_PERCENT and 'USDT' in symbol:
                    result_queue.put((symbol, percent_change))
            
def smq():
    data_queue = Queue()
    result_queue = Queue()
    fetcher = Process(target=fetch_data, args=(data_queue,))
    processor1 = Process(target=process_data, name='process1', args=(data_queue, result_queue, 60))
    processor2 = Process(target=process_data, name='process2', args=(data_queue, result_queue, 30))
    processor3 = Process(target=process_data, name='process3', args=(data_queue, result_queue, 10))
    processor4 = Process(target=process_data, name='process4', args=(data_queue, result_queue, 5))
    fetcher.start()
    processor1.start()
    processor2.start()
    processor3.start()
    processor4.start()

    try:
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
    except KeyboardInterrupt:
        fetcher.terminate()
        processor1.terminate()
        processor2.terminate()
        processor3.terminate()
        processor4.terminate()

        fetcher.join()
        processor1.join()
        processor2.join()
        processor3.join()
        processor4.join()

# if __name__ == '__main__':
#     while True:
#         signal = smq()
#         print(signal)