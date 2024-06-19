from prsrppp import prsrpp
from name import get_balance, get_ticker, place_order, get_last_price, get_roundQty, klineValidation, ordersClear
from pprint import pprint
import time
import multiprocessing

headers = {'User-Agent': 'Opera/9.80 (Windows NT 6.2; WOW64) Presto/2.12.388 Version/12.17'}
with open('urlCount.txt', 'r', encoding='utf-8') as f:
    url_count = int(f.read())
tp = 0.012
sl = 0.030

def main():
    global headers, tp, sl, url_count
    while True:
        try:
            timeNow = int(time.time())
            url = f'https://t.me/pump_dump_screener_demo/{url_count}'
            content = prsrpp(url, headers, url_count=url_count)
            url_count += 1
                    
            ticker_tickers = get_ticker(content)
            balance_usdt = get_balance()
            balanceWL = float(balance_usdt)
            mark_price = get_last_price(ticker_tickers[0])
            roundQty =  get_roundQty(ticker_tickers[0])
            if ticker_tickers[0] in ticker_tickers[1]:
                if str(content).count('🔴') == 1:
                    side = klineValidation(ticker_tickers[0], 'Buy', mark_price, roundQty, timeNow)
                    place_order(ticker_tickers[0], side, mark_price, roundQty, balanceWL, tp, sl)
                if str(content).count('🟢') == 1:
                    side = klineValidation(ticker_tickers[0], 'Sell', mark_price, roundQty, timeNow)
                    place_order(ticker_tickers[0], side, mark_price, roundQty, balanceWL, tp, sl)

            # Сохранение значений в текстовой файл
            with open('urlCount.txt', 'w', encoding='utf-8') as f:
                f.write(str(url_count))
            with open('urlCount.txt', 'r', encoding='utf-8') as f:
                url_count = int(f.read())
            break
        except Exception as er:
            pprint(er)

process1 = multiprocessing.Process(target=ordersClear, name='BMQ-V2-ORDERSCLEAR-1')
process2 = multiprocessing.Process(target=main, name='BMQ-V2-TEST-1')
if __name__ == '__main__':
    process1.start()
    process2.start()
