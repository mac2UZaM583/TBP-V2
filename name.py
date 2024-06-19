from keys import api_key, api_secret
from pybit.unified_trading import HTTP
import numpy as np
from decimal import Decimal
from datetime import datetime
import time
from pprint import pprint

session = HTTP(
    # demo=True,
    api_key=api_key,
    api_secret=api_secret
)

# Получение баланса
def get_balance():
    response = session.get_wallet_balance(accountType='CONTRACT', coin='USDT')
    balance = response['result']['list'][0]['coin'][0]['walletBalance']
    return balance

# Получение тикера
def get_ticker(content):
    elements = str(content).split()
    ticker = str(elements[1][11:-1] + 'USDT')
    tickersNoneValidate = session.get_tickers(category='linear')['result']['list']
    tickers = [ticker['symbol'] for ticker in tickersNoneValidate if 'USDT' in ticker['symbol'] and not 'USDC' in ticker['symbol']]
    if ticker not in tickers:
        for t in tickers:
            if ticker in t:
                prefix = t.split(ticker)[0]
                if prefix.isdigit() and '0' in prefix:
                    return prefix + ticker
    else:
        return ticker
    
# Получение информации о текущей последней цене
def get_last_price(symbol):
    response = session.get_tickers(category='linear', symbol=symbol)
    mark_price = float(response['result']['list'][0]['lastPrice'])
    return mark_price

# Получение информации о лотсайзфильтре ордера
def get_roundQty(symbol):
    mark_price = get_last_price(symbol)
    data_minroundQty = session.get_instruments_info(category='linear', symbol=symbol)
    data_minroundQty_2 = data_minroundQty['result']['list'][0]['lotSizeFilter']['minOrderQty']
    roundQty_forTPSL = len(str(mark_price).split('.')[-1]) if '.' in str(data_minroundQty) else 0
    roundQty_forOrder = len(str(data_minroundQty_2).split('.')[-1]) if '.' in str(data_minroundQty_2) else 0
    return roundQty_forTPSL, roundQty_forOrder

# Получение уровня поддержки и сопротивления
def getSR(symbol, roundQty):
    klines = session.get_kline(symbol=symbol, category='linear', interval='60', limit=360)['result']['list']
    closes = np.unique(np.array([float(kline[4]) for kline in klines]))
    lowest = np.sort(closes)[::5]
    values = np.diff(lowest)
    valueMax = np.round(np.max(values), roundQty[0])

    # Разделение значений по спискам и определение среднего значения
    split_index = np.argmax(np.round(values, roundQty[0]) == valueMax) + 1
    support_level = np.round(np.mean(lowest[:split_index]), roundQty[0])
    resistance_level = np.round(np.mean(lowest[split_index:]), roundQty[0])
    return support_level, resistance_level

# Валидация клайна
def klineValidation(symbol, side, markPrice, roundQty, timeNow):
    print(f'Создание позиции для {symbol} ')
    klines1MinTime = session.get_kline(symbol=symbol, category='linear', interval='1', limit=1)['result']['list'][0]
    klineCreateTime = int(klines1MinTime[0][:-3])
    
    # Проверка ведущего клайна
    if timeNow > klineCreateTime:
        run = True
        while run:
            print(f'run #1')
            klines1MinTimeNext = session.get_kline(symbol=symbol, category='linear', interval='1', limit=1)['result']['list'][0]
            time.sleep(0.3)
            if klines1MinTime[0] != klines1MinTimeNext[0]:
                run = False
        # Проверка следущего клайна
        run = True
        while run:
            print(f'run #2')
            klines1MinTimeNext1 = session.get_kline(symbol=symbol, category='linear', interval='1', limit=1)['result']['list'][0]
            time.sleep(0.3)
            if klines1MinTimeNext[0] != klines1MinTimeNext1[0]:
                klines1MinTimeNext = session.get_kline(symbol=symbol, category='linear', interval='1', limit=2)['result']['list'][1]
                run = False
        print(f'run completed^ {run}')
        
        # Определение валидности и выдача стороны сделки 
        support_level, resistance_level = getSR(symbol, roundQty)
        markPriceS = markPrice - ((markPrice / 100) * 1.5)
        markPriceR = markPrice + ((markPrice / 100) * 1.5)
        klineRadius = Decimal(klines1MinTimeNext[2]) - Decimal(klines1MinTimeNext[3])
        if side == 'Sell':
            if Decimal(klines1MinTimeNext[1]) > Decimal(klines1MinTimeNext[4]):
                if Decimal(klines1MinTimeNext[4]) - Decimal(klines1MinTimeNext[3]) < klineRadius - (klineRadius * Decimal(60 / 100)):
                    if markPriceS > support_level:
                        return side
                    else:
                        print('сделка не валидна')
                        return None
        elif side == 'Buy':
            if Decimal(klines1MinTimeNext[1]) < Decimal(klines1MinTimeNext[4]):
                if Decimal(klines1MinTimeNext[4]) - Decimal(klines1MinTimeNext[3]) > klineRadius - (klineRadius * Decimal(40 / 100)):
                    if markPriceR < resistance_level:
                        return side
                    else:
                        print('сделка не валидна')
                        return None

# Очистка ордеров
def ordersClear():
    n = 0
    with open('orderId.txt', 'r', encoding='utf-8') as f:
        orderId_copy = [f.read()]
    while True:
        try:
            n += 1
            print(f'Очистка ордеров. Запрос номер - {n}')
            orderId = session.get_closed_pnl(category='linear', page=1)
            orderId = orderId['result']['list'][0]['orderId']
            if len(session.get_positions(category='linear', settleCoin='USDT')['result']['list']) == 0:
                if orderId != orderId_copy[0]:
                    orderId_copy.clear()
                    orderId_copy.append(orderId)
                    with open('orderId.txt', 'w', encoding='utf-8') as f:
                        f.write(orderId)
                    pprint(session.cancel_all_orders(
                        category="linear",
                        settleCoin='USDT'
                    ))
            time.sleep(0.5)
        except Exception as er:
            with open('errorsOrdersClear.txt', 'a', encoding='utf-8') as f:
                f.write(f'{datetime.now()} |{er}\n\n')

# Публикация ордера
def place_order(symbol, side, mark_price, roundQty, balanceWL, tp, sl):
    try:
        if len(session.get_open_orders(category='linear', settleCoin='USDT')['result']['list']) == 0:
            qty = round(balanceWL / mark_price, roundQty[1])
            if side == 'Sell':
                tp_priceL = round((1 - tp) * mark_price, roundQty[0])
            elif side == 'Buy':
                tp_priceL = round((1 + tp) * mark_price, roundQty[0])

            # Выставление маркет ордера
            print(
                f'Placing {side} order for {symbol} \n'
                f'TpPrice: {tp_priceL}\n'
                f'Qty: {qty}\n' 
                f'RoundQty: {roundQty}\n'
                f'Time: {datetime.now()}'
            )
            try:
                pprint(session.switch_margin_mode(
                    category="linear",
                    symbol=symbol,
                    tradeMode=0,
                    buyLeverage="10",
                    sellLeverage="10",
                ))
            except Exception as er:
                print(f'не удалось сменить режим сделки потому что и так все хорошо \n\n {er}')
            resp = session.place_order(
                category='linear',
                symbol=symbol,
                qty=qty,
                marketUnit='baseCoin',
                side=side,
                orderType='Market',
                takeProfit=tp_priceL,
                isLeverage=10,
                tpTriggerBy='LastPrice',
                slTriggerBy='LastPrice'
            )
            pprint(resp)

            # Более точное выставление тп и сл ордеров
            entryPrice = round(Decimal(session.get_positions(
                category='linear',
                symbol=symbol
            )['result']['list'][0]['avgPrice']), roundQty[0])
            entryPriceRadius = entryPrice - (entryPrice * Decimal(0.96))
            if side == 'Sell':
                entryPrice2 = round(entryPrice + entryPriceRadius, roundQty[0])
                entryPrice3 = round(entryPrice2 + entryPriceRadius, roundQty[0])
                entryPrice4 = round(entryPrice3 + entryPriceRadius, roundQty[0])
                entryPrice5 = round(entryPrice4 + entryPriceRadius, roundQty[0])
                tp_priceL = round(Decimal(1 - tp) * Decimal(entryPrice), roundQty[0])
                tp_priceL2 = round(Decimal(1 - 0.007) * Decimal(entryPrice2), roundQty[0])
                tp_priceL3 = round(Decimal(1 - 0.0048) * Decimal(entryPrice3), roundQty[0])
                tp_priceL4 = round(Decimal(1 - 0.0036) * Decimal(entryPrice4), roundQty[0])
                tp_priceL5 = round(Decimal(1 - 0.003) * Decimal(entryPrice5), roundQty[0])
                sl_price = round(Decimal(1 + sl) * Decimal(entryPrice5), roundQty[0])
            elif side == 'Buy':
                entryPrice2 = round(entryPrice - entryPriceRadius, roundQty[0])
                entryPrice3 = round(entryPrice2 - entryPriceRadius, roundQty[0])
                entryPrice4 = round(entryPrice3 - entryPriceRadius, roundQty[0])
                entryPrice5 = round(entryPrice4 - entryPriceRadius, roundQty[0])
                tp_priceL = round(Decimal(1 + tp) * Decimal(entryPrice), roundQty[0])
                tp_priceL2 = round(Decimal(1 + 0.007) * Decimal(entryPrice2), roundQty[0])
                tp_priceL3 = round(Decimal(1 + 0.0048) * Decimal(entryPrice3), roundQty[0])
                tp_priceL4 = round(Decimal(1 + 0.0036) * Decimal(entryPrice4), roundQty[0])
                tp_priceL5 = round(Decimal(1 + 0.003) * Decimal(entryPrice5), roundQty[0])
                sl_price = round(Decimal(1 - sl) * Decimal(entryPrice5), roundQty[0])
            try:
                print(session.set_trading_stop(
                    category='linear',
                    symbol=symbol,
                    tpslMode='Full',
                    takeProfit=tp_priceL,
                    positionIdx=0
                ))
            except:
                print('тп не установлен потому что и так все хорошо')

            # Публикация лимитных ордеров
            resp2 = session.place_order(
                category='linear',
                symbol=symbol,
                qty=qty,
                marketUnit='baseCoin',
                side=side,
                orderType='Limit',
                price=str(entryPrice2),
                takeProfit=tp_priceL2,
                isLeverage=10,
                tpTriggerBy='LastPrice',
                slTriggerBy='LastPrice'
            )
            print('первый лимитный ордер установлен')
            resp3 = session.place_order(
                category='linear',
                symbol=symbol,
                qty=qty,
                marketUnit='baseCoin',
                side=side,
                orderType='Limit',
                price=str(entryPrice3),
                takeProfit=tp_priceL3,
                isLeverage=10,
                tpTriggerBy='LastPrice',
                slTriggerBy='LastPrice'
            )
            print('второй лимитный ордер установлен')
            resp4 = session.place_order(
                category='linear',
                symbol=symbol,
                qty=qty,
                marketUnit='baseCoin',
                side=side,
                orderType='Limit',
                price=str(entryPrice4),
                takeProfit=tp_priceL4,
                isLeverage=10,
                tpTriggerBy='LastPrice',
                slTriggerBy='LastPrice'
            )
            print('третий лимитный ордер установлен')
            resp5 = session.place_order(
                category='linear',
                symbol=symbol,
                qty=qty,
                marketUnit='baseCoin',
                side=side,
                orderType='Limit',
                price=str(entryPrice5),
                takeProfit=tp_priceL5,
                stopLoss=sl_price,
                isLeverage=10,
                tpTriggerBy='LastPrice',
                slTriggerBy='LastPrice'
            )
            print('четвертый лимитный ордер установлен')
            print(f'{resp2}\n\n{resp3}\n\n{resp4}\n\n{resp5}\n\n')
    except Exception as er:
        print(er, 'Place order')
        with open('errors.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now()} | {er}\n\n')


