from keys import api_key, api_secret
from pybit.unified_trading import HTTP
import numpy as np
from decimal import Decimal as D
from datetime import datetime
import time
from pprint import pprint

session = HTTP(
    demo=True,
    api_key=api_key,
    api_secret=api_secret
)

# Получение баланса
def get_balance():
    response = session.get_wallet_balance(accountType='UNIFIED', coin='USDT')
    balance = response['result']['list'][0]['coin'][0]['walletBalance']
    return balance
    
# Получение информации о текущей последней цене
def get_last_price(symbol):
    response = session.get_tickers(category='linear', symbol=symbol)
    mark_price = float(response['result']['list'][0]['lastPrice'])
    return mark_price

# Получение информации о лотсайзфильтре ордера
def get_roundQty(symbol):
    data_minroundQty = session.get_instruments_info(category='linear', symbol=symbol)['result']['list'][0]['lotSizeFilter']['minOrderQty']
    data_minroundPrice = session.get_instruments_info(category='linear', symbol=symbol)['result']['list'][0]['priceFilter']['minPrice']
    roundForQty = len(data_minroundQty) if D(data_minroundQty) < 1 else 0
    roundForTPSL = (len(data_minroundPrice) - 2) if D(data_minroundPrice) < 1 else len(data_minroundPrice)
    return roundForTPSL, roundForQty

# Получение уровня поддержки и сопротивления
def getSR(symbol, roundQty):
    klines = session.get_kline(symbol=symbol, category='linear', interval='60', limit=360)['result']['list']
    closes = np.unique(np.array([float(kline[4]) for kline in klines]))
    lowestGlobal = np.sort(closes)[::5]
    lowestLocal = np.sort(closes)[:100:3]
    valuesGlobal = np.diff(lowestGlobal)
    valuesLocal = np.diff(lowestLocal)
    valueMaxGlobal = np.round(np.max(valuesGlobal), roundQty[0])
    valueMaxLocal = np.round(np.max(valuesLocal), roundQty[0])

    # Разделение значений по спискам и определение среднего значения
    split_indexGlobal = np.argmax(np.round(valuesGlobal, roundQty[0]) == valueMaxGlobal) + 1
    split_indexLocal = np.argmax(np.round(valuesLocal, roundQty[0]) == valueMaxLocal) + 1
    support_levelGlobal = np.round(np.mean(lowestGlobal[:split_indexGlobal]), roundQty[0])
    resistance_levelGlobal = np.round(np.mean(lowestGlobal[split_indexGlobal:]), roundQty[0])
    support_levelLocal = np.round(np.mean(lowestLocal[:split_indexLocal]), roundQty[0])
    resistance_levelLocal = np.round(np.mean(lowestLocal[split_indexLocal:]), roundQty[0])
    return support_levelGlobal, resistance_levelGlobal, support_levelLocal, resistance_levelLocal

# Валидация клайна
def klineValidation(symbol, side, roundQty, timeNow):
    klines = len(session.get_kline(symbol=symbol, category='linear', interval='60', limit=240)['result']['list'])
    klines1MinTime = session.get_kline(symbol=symbol, category='linear', interval='1', limit=1)['result']['list'][0]
    klineCreateTime = int(klines1MinTime[0][:-3])
    
    # Проверка ведущего клайна
    if timeNow > klineCreateTime and klines >= 240:
        run = True
        while run:
            print(f'Run #1')
            klines1MinTimeNext = session.get_kline(symbol=symbol, category='linear', interval='1', limit=1)['result']['list'][0]
            time.sleep(0.3)
            if klines1MinTime[0] != klines1MinTimeNext[0]:
                run = False
        # Проверка следущего клайна
        run = True
        while run:
            print(f'Run #2')
            klines1MinTimeNext1 = session.get_kline(symbol=symbol, category='linear', interval='1', limit=1)['result']['list'][0]
            time.sleep(0.3)
            if klines1MinTimeNext[0] != klines1MinTimeNext1[0]:
                klines1MinTimeNext = session.get_kline(symbol=symbol, category='linear', interval='1', limit=2)['result']['list'][1]
                run = False
        print(f'Run completed^ {run}')
        
        # Определение валидности и выдача стороны сделки 
        SGlobal, RGlobal, SLocal, RLocal = getSR(symbol, roundQty)
        markPrice = get_last_price(symbol)
        markPriceS = markPrice - ((markPrice / 100) * 1.5)
        markPriceR = markPrice + ((markPrice / 100) * 1.5)
        klineRadius = D(klines1MinTimeNext[2]) - D(klines1MinTimeNext[3])
        CloseOpenRadius = D(klines1MinTimeNext[4]) - D(klines1MinTimeNext[3])
        if side == 'Sell':
            ThresholdRadiusSell = round(klineRadius - (klineRadius * D(60 / 100)), roundQty[0])
            if (D(klines1MinTimeNext[1]) > D(klines1MinTimeNext[4])) and (CloseOpenRadius < ThresholdRadiusSell) and (markPriceS > SGlobal or markPriceS > SLocal):
                return side
            else:
                with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
                    f.write(f'BMQ: Ордер не прошел проверку.\n'
                            f'SGlobal: {SGlobal}, SLocal: {SLocal}\n'
                            f'MarkPriceS: {markPriceS}, MarkPrice: {markPrice}\n'
                            f'KlinesOpen: {klines1MinTimeNext[1]}, KlinesClose: {klines1MinTimeNext[4]}\n'
                            f'CloseOpenRadius: {CloseOpenRadius}, ThresholdRadiusSell: {ThresholdRadiusSell}\n'
                            f'Время - {datetime.now()}')
                return None
        elif side == 'Buy':
            ThresholdRadiusBuy = round(klineRadius - (klineRadius * D(40 / 100)), roundQty[0])
            if (D(klines1MinTimeNext[1]) < D(klines1MinTimeNext[4])) and (CloseOpenRadius > ThresholdRadiusBuy) and (markPriceR < RGlobal or markPriceR < RLocal):
                return side
            else:
                with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
                    f.write(f'BMQ: Ордер не прошел проверку.\n'
                            f'RGlobal: {RGlobal}, RLocal: {RLocal}\n'
                            f'MarkPriceR: {markPriceR}, MarkPrice: {markPrice}\n'
                            f'KlinesOpen: {klines1MinTimeNext[1]}, KlinesClose: {klines1MinTimeNext[4]}\n'
                            f'CloseOpenRadius: {CloseOpenRadius}, ThresholdRadiusSell: {ThresholdRadiusBuy}\n'
                            f'Время - {datetime.now()}')
                return None
    else:
        with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
            f.write(f'BMQ: Ордер не прошел проверку.\n'
                    f'Время клайна - {klineCreateTime}\n'
                    f'Время записи - {timeNow}\n'
                    f'Klines: {klines}')

# Очистка ордеров
def ordersClear():
    n = 0
    with open('orderId.txt', 'r', encoding='utf-8') as f:
        orderId_copy = [f.read()]
    while True:
        try:
            n += 1
            print(f'Очистка ордеров. Запрос номер: {n}')
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
            time.sleep(3)
        except Exception as er:
            with open('errorsOrdersClear.txt', 'a', encoding='utf-8') as f:
                f.write(f'{datetime.now()} |{er}\n\n')

# Публикация ордера
def place_order(symbol, side, roundQty, balanceWL, tp, sl):
    try:
        if len(session.get_open_orders(category='linear', settleCoin='USDT')['result']['list']) == 0:
            mark_price = get_last_price(symbol)
            qty = round(balanceWL / mark_price, roundQty[1])
            if side == 'Sell':
                tp_priceL = round((1 - tp) * mark_price, roundQty[0])
            elif side == 'Buy':
                tp_priceL = round((1 + tp) * mark_price, roundQty[0])

            # Выставление маркет ордера
            try:
                pprint(session.switch_margin_mode(
                    category="linear",
                    symbol=symbol,
                    tradeMode=0,
                    buyLeverage="10",
                    sellLeverage="10",
                ))
            except Exception as er:
                print(f'{er}\n Не удалось сменить режим торговли\n\n\n')
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
            entryPrice = round(D(session.get_positions(
                category='linear',
                symbol=symbol
            )['result']['list'][0]['avgPrice']), roundQty[0])
            entryPriceRadius = entryPrice - (entryPrice * D(0.96))
            if side == 'Sell':
                entryPrice2 = round(entryPrice + entryPriceRadius, roundQty[0])
                entryPrice3 = round(entryPrice2 + entryPriceRadius, roundQty[0])
                entryPrice4 = round(entryPrice3 + entryPriceRadius, roundQty[0])
                entryPrice5 = round(entryPrice4 + entryPriceRadius, roundQty[0])
                tp_priceL = round(D(1 - tp) * D(entryPrice), roundQty[0])
                tp_priceL2 = round(D(1 - 0.007) * D(entryPrice2), roundQty[0])
                tp_priceL3 = round(D(1 - 0.0048) * D(entryPrice3), roundQty[0])
                tp_priceL4 = round(D(1 - 0.0036) * D(entryPrice4), roundQty[0])
                tp_priceL5 = round(D(1 - 0.003) * D(entryPrice5), roundQty[0])
                sl_price = round(D(1 + sl) * D(entryPrice5), roundQty[0])
            elif side == 'Buy':
                entryPrice2 = round(entryPrice - entryPriceRadius, roundQty[0])
                entryPrice3 = round(entryPrice2 - entryPriceRadius, roundQty[0])
                entryPrice4 = round(entryPrice3 - entryPriceRadius, roundQty[0])
                entryPrice5 = round(entryPrice4 - entryPriceRadius, roundQty[0])
                tp_priceL = round(D(1 + tp) * D(entryPrice), roundQty[0])
                tp_priceL2 = round(D(1 + 0.007) * D(entryPrice2), roundQty[0])
                tp_priceL3 = round(D(1 + 0.0048) * D(entryPrice3), roundQty[0])
                tp_priceL4 = round(D(1 + 0.0036) * D(entryPrice4), roundQty[0])
                tp_priceL5 = round(D(1 + 0.003) * D(entryPrice5), roundQty[0])
                sl_price = round(D(1 - sl) * D(entryPrice5), roundQty[0])
            try:
                print(session.set_trading_stop(
                    category='linear',
                    symbol=symbol,
                    tpslMode='Full',
                    takeProfit=tp_priceL,
                    positionIdx=0
                ))
            except:
                print('Тейк профит не переустановлен')

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
            print('\n\n\n1 лимитный ордер установлен\n\n\n')
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
            print('2 лимитный ордер установлен\n\n\n')
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
            print('3 лимитный ордер установлен\n\n\n')
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
            print('4 лимитный ордер установлен\n\n\n')
            print(f'{resp2}\n\n{resp3}\n\n{resp4}\n\n{resp5}\n\n')
    except Exception as er:
        with open('/CODE_PROJECTS/SMQ-N & Python/signal.txt', 'w', encoding='utf-8') as f:
            f.write(f'Ошибка в Place Order: \n{er}\n Время: {datetime.now()}')


