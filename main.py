import requests
from bs4 import BeautifulSoup
from datetime import datetime
from name import get_balance, get_tickers, find_tickerDone, place_order, get_last_price, get_roundQty, getNextKline, ordersClear
from pprint import pprint
import multiprocessing

headers = {'User-Agent': 'Opera/9.80 (Windows NT 6.2; WOW64) Presto/2.12.388 Version/12.17'}
with open('urlCount.txt', 'r', encoding='utf-8') as f:
    url_count = int(f.read())
tp = 0.012
sl = 0.030
i = 0

def main():
    global headers, tp, sl, i, url_count
    # Инициализация контроля программы засчет цикла
    while True:
        try:
            while True:
                try:
                    url = f'https://t.me/pump_dump_screener_demo/{url_count}'
                    # Получание данных из http запроса
                    try:
                        response = requests.get(url, headers)
                    except:
                        print('ошибка. повторение запроса/время: ', datetime.now())
                        response = requests.get(url, headers)
                    soup = BeautifulSoup(response.text, 'lxml')
                    data = soup.find_all('meta')
                    # Принятие решения о стороне сделки
                    for content in data:
                        if '🔴' in str(content) or '🟢' in str(content):
                            print(f'проверка в html контента. время - {datetime.now()}')
                            elements = str(content).split()
                            ticker = str(elements[1][11:-1] + 'USDT')
                            tickers = get_tickers()
                            tickerDone = find_tickerDone(ticker, tickers)
                            url_count += 1
                            balance_usdt = get_balance()
                            balanceWL = float(balance_usdt)
                            mark_price = get_last_price(tickerDone)
                            roundQty =  get_roundQty(tickerDone)

                            if str(content).count('🔴') == 1:
                                if tickerDone in tickers and balance_usdt != 0:
                                    side = getNextKline(tickerDone, 'Buy', mark_price, roundQty)
                                    side = 'Buy'
                                    place_order(tickerDone, side, mark_price, roundQty, balanceWL, tp, sl)
                            if str(content).count('🟢') == 1:
                                if tickerDone in tickers and balance_usdt != 0:
                                    side = getNextKline(tickerDone, 'Sell', mark_price, roundQty)
                                    side = 'Sell'
                                    place_order(tickerDone, side, mark_price, roundQty, balanceWL, tp, sl)
                            
                            # Сохранение значений в текстовой файл
                            with open('urlCount.txt', 'w', encoding='utf-8') as f:
                                f.write(str(url_count))
                            with open('urlCount.txt', 'r', encoding='utf-8') as f:
                                url_count = int(f.read())
                            break

                    i += 1
                    print(i, datetime.now(), url_count)
                except Exception as er:
                    pprint(er, datetime.now())
        except Exception as er:
            pprint(er)

process1 = multiprocessing.Process(target=ordersClear, name='BMQ-V2-ORDERSCLEAR-1')
process2 = multiprocessing.Process(target=main, name='BMQ-V2-TEST-1')
if __name__ == '__main__':
    process1.start()
    process2.start()
