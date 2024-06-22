from smq import smq
from name import get_balance, place_order, get_roundQty, klineValidation, ordersClear, TPSL
from pprint import pprint
import time
from multiprocessing import Process

tp = 0.012
sl = 0.030

def main():
    global headers, tp, sl
    while True:
        try:
            while True:
                try:
                    print(f'\n\nstart/time - плдюююююю\n\n')                    
                    signal = smq()  
                            
                    timeNow = int(time.time())
                    balance_usdt = get_balance()
                    balanceWL = float(balance_usdt)
                    roundQty =  get_roundQty(signal[0])
                    if signal[1] < 0:
                        side = klineValidation(signal[0], 'Buy', roundQty, timeNow)
                        if side != None:
                            place_order(signal[0], side, roundQty, balanceWL, tp, sl)
                    if signal[1] > 0:
                        side = klineValidation(signal[0], 'Sell', roundQty, timeNow)
                        if side != None:
                            place_order(signal[0], side, roundQty, balanceWL, tp, sl)
                    break
                except Exception as er:
                    pprint(er)
        except Exception as er:
            pprint(er)

process1 = Process(target=ordersClear, name='BMQ-V2-ORDERSCLEAR-1')
process2 = Process(target=TPSL, name='BMQ-V2-TPSL_limit_orders')
process3 = Process(target=main, name='BMQ-V2-TEST-1')
if __name__ == '__main__':
    process1.start()
    process2.start()
    process3.start()
