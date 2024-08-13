from session import session
from settings__ import files_content
from notifications import log_decorator

import traceback
from pprint import pprint

def s_round(value, round):
    if value != '':
        lst = str(f'{float(value):.{20}f}').split('.')
        if len(lst) > 1:
            lst[1] = lst[1][:round]
        if round > 0:
            return '.'.join(lst).rstrip('0')
        return ''.join(lst).rstrip('0')
    return value

def s_cancel_position():
    try:
        session.cancel_all_orders(category='linear', settleCoin='USDT')
        order = session.get_positions(category='linear', settleCoin='USDT', limit=1)['result']['list'][0]
        session.place_order(
            category='linear',
            symbol=order['symbol'],
            side='Buy' if order['side'] == 'Sell' else 'Sell',
            orderType='Market',
            reduceOnly=True,
            qty=0
        )
    except:
        # traceback.print_exc()
        pass

async def s_tp(
    tp_arr, 
    tp_price_position, 
    side, 
    round_price, 
    avg_price, 
    limits_num, 
    symbol
):    
    tp_price = s_round(
        avg_price + (tp_arr[-limits_num] * (-1 if side == 'Sell' else 1) * avg_price),
        round_price
    )
    if tp_price_position != tp_price:
        try:
            session.set_trading_stop(
                category='linear', 
                symbol=symbol, 
                tpslMode='Full', 
                takeProfit=tp_price, 
                positionIdx=0
            )
        except:
            traceback.print_exc()

async def s_sl(
    sl,
    sl_price_position, 
    side,
    round_price, 
    avg_price,
    limits_num,
    symbol
):
    if limits_num < 1:
        print(limits_num, 'sl')
        sl_price = s_round(
            avg_price + (sl * (1 if side == 'Sell' else -1) * avg_price),
            round_price
        )
        if sl_price_position != sl_price:
            try:
                session.set_trading_stop(
                    category='linear', 
                    symbol=symbol, 
                    tpslMode='Full', 
                    stopLoss=sl_price, 
                    positionIdx=0
                )
            except:
                traceback.print_exc()
    elif sl_price_position != '':
        try:
            session.set_trading_stop(
                category='linear', 
                symbol=symbol, 
                tpslMode='Full', 
                stopLoss=0, 
                positionIdx=0
            )
        except:
            traceback.print_exc()

async def place_order(symbol, qty, side):
    pprint(session.place_order(
        category='linear',
        symbol=symbol,
        qty=qty, 
        marketUnit='baseCoin',
        side=side,
        orderType='Market'
    ))

async def place_orders_limits(
    symbol, 
    price,
    limit_price_changes, 
    qty, 
    volume_multiplier,
    round,
    side
):
    pprint(session.place_batch_order(
        category='linear',
        request=[
            {
                'symbol': symbol,
                'qty': s_round(volume_multiplier ** (i + 1) * qty, round[0]), 
                'marketUnit': 'baseCoin',
                'side': side,
                'orderType': 'Limit',
                'price': s_round(
                    ((price * limit_price_changes[i]) * (1 if side == 'Sell' else -1)) + price, 
                    round[1]
                )
            }
            for i in range(int(files_content['AVERAGING_QTY']))
        ]
    ))

def s_pre_main():
    s_cancel_position()
    for value in session.get_tickers(
        category='linear'
    )['result']['list']:
        if files_content['MODE'].upper() == 'DEMO':
            try:
                symbol = value['symbol']
                print(symbol)
                session.set_leverage(
                    category='linear', 
                    symbol=symbol,
                    buyLeverage='10',
                    sellLeverage='10'
                )
            except:
                pass
        else:
            try:
                symbol = value['symbol']
                print(symbol)
                session.switch_margin_mode(
                    category='linear', 
                    symbol=symbol, 
                    tradeMode=1,
                    buyLeverage='10',
                    sellLeverage='10'
                )
            except:
                pass

if __name__ == '__main__':
    s_pre_main()
    # s_cancel_position()
    # pprint(session.get_positions(category='linear', settleCoin='USDT', limit=1)['result']['list'][0])