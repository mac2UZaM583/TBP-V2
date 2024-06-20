from smq import smq
from name import get_balance, place_order, get_last_price, get_roundQty, klineValidation, ordersClear
from pprint import pprint
import time
import multiprocessing

tp = 0.012
sl = 0.030

def main():
    global headers, tp, sl, url_count
    while True:
        try:
            while True:
                try:
                    timeNow = int(time.time())
                    print(f'\n\nstart/time {timeNow}\n\n')
                    
                    signal = smq()
                    balance_usdt = get_balance()
                    balanceWL = float(balance_usdt)
                    mark_price = get_last_price(signal[0])
                    roundQty =  get_roundQty(signal[0])
                    if signal[1] < 0:
                        print(f'Long {signal[0], signal[1]}%')
                        side = klineValidation(signal[0], 'Buy', mark_price, roundQty, timeNow)
                        place_order(signal[0], side, mark_price, roundQty, balanceWL, tp, sl)
                    if signal[1] > 0:
                        print(f'Short {signal[0], signal[1]}%')
                        side = klineValidation(signal[0], 'Sell', mark_price, roundQty, timeNow)
                        place_order(signal[0], side, mark_price, roundQty, balanceWL, tp, sl)
                    signal = None

                    # Сохранение значений в текстовой файл
                    with open('urlCount.txt', 'w', encoding='utf-8') as f:
                        f.write(str(url_count))
                    with open('urlCount.txt', 'r', encoding='utf-8') as f:
                        url_count = int(f.read())
                    break
                except Exception as er:
                    pprint(er)
        except Exception as er:
            pprint(er)
            continue

process1 = multiprocessing.Process(target=ordersClear, name='BMQ-V2-ORDERSCLEAR-1')
process2 = multiprocessing.Process(target=main, name='BMQ-V2-TEST-1')
if __name__ == '__main__':
    process1.start()
    process2.start()
