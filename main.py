from set import *
from get import *
from settings__ import files_content
from session import session
from notifications import s_send_n

import asyncio
import time
import traceback
from datetime import datetime
from itertools import count

averaging_qty = int(files_content['AVERAGING_QTY'])
count_ = count(0, 1)

async def main():
    while True:
        try:
            start = time.time()
            percent_changes_old = g_last_prices()
            while time.time() - start < float(files_content['CYCLE_UPDATE']):
                print(f'cycle {next(count_)}')
                positions, limits_num = await asyncio.gather(
                    g_positions(),
                    asyncio.to_thread(lambda: len(tuple(filter(
                        lambda v: v['orderType'] == 'Limit', 
                        session.get_open_orders(
                            category='linear',
                            settleCoin='USDT'
                        )['result']['list']
                    ))))
                )
                if positions:
                    position = positions[0]
                    symbol = position['symbol']
                    round_ = await g_round_qty(symbol)
                    round_price = round_[1]
                    await asyncio.gather(
                        s_tp(
                            np.array((0.025, 0.007, *np.full(averaging_qty - 2, 0.02))),
                            position['takeProfit'],
                            position['side'],
                            round_price,
                            float(position['avgPrice']),
                            limits_num,
                            symbol
                        ),
                        s_sl(
                            float(files_content['STOP_LOSS']),
                            position['stopLoss'],
                            position['side'],
                            round_price,
                            float(position['avgPrice']),
                            limits_num,
                            symbol
                        ),
                        s_switch_pos_mode(symbol, limits_num)
                    )
                elif positions == []:
                    session.cancel_all_orders(category='linear', settleCoin='USDT')

                global percent_change
                percent_change = g_percent_change(*percent_changes_old)
                if percent_change:
                    time_percent = int(int(time.time()) * 1000)
                    s_send_n(
                        f'PC::\n\n'
                        f'{percent_change[0]}, {round(percent_change[1] * 100, 2)}%\n'
                        f'{datetime.now()}'
                    )
                    break
            
            '''SET ⭣
            '''
            if percent_change and positions == []:
                symbol, changes = percent_change
                # side = 'Buy' if changes < 0 else 'Sell'
                side_non_validated = 'Buy' if changes < 0 else 'Sell'
                side = g_side_validated(symbol, side_non_validated, time_percent)
                if side:
                    round_qty, price, balance = await g_data(symbol)
                    qty = ((balance / price) * 0.011) * int(files_content['LEVERAGE'])
                    await asyncio.gather(
                        place_order(
                            symbol, 
                            s_round(qty, round_qty[0]),
                            side
                        ),
                        place_orders_limits(
                            symbol, 
                            price,
                            (0.04, *np.arange(1, averaging_qty) * 0.08),
                            qty,
                            float(files_content['VOLUME_MULTIPLIER']),
                            round_qty,
                            side
                        )
                    )
                s_send_n(
                    f'SIDE::\n\n'
                    f'{side}'
                )
        except:
            s_send_n(
                f'TRACEBACK::\n\n'
                f'{traceback.format_exc()}'
            )

# s_pre_main()
asyncio.run(main()) #⭠⭡⭢⭣⭤ ⭥⮂⮃