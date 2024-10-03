import numpy as np
from indications import *

def g_pack_data(klines):
    data = pd.DataFrame({
        'close': klines[:, 4],
        'high': klines[:, 2],
        'low': klines[:, 3],
    })
    data['RSI'] = g_rsi(data)
    data['ADX'] = g_adx(data['high'], data['low'], data['close'])
    data['CCI'] = g_cci(data)
    data['WT'] = g_williams_r(data['high'], data['low'], data['close'])
    data['Distances'] = g_lorentzian_distance_s({
        'f1': data['RSI'].values,
        'f2': data['WT'].values,
        'f3': data['CCI'].values,
        'f4': data['ADX'].values,
    }, len(data))
    for el in data:
        data[el] = data[el].fillna(data[el].mean())
    return data

def g_train_test_split(
    x, 
    y,
    test=False,
    train_size=0.8,
):  
    split_func = lambda v, len_: tuple(
        v[i][len_:] 
        if i % 2 != 0 
        else v[i][:len_]
        for i in range(4) 
    )
    tple = (x, x, y, y)
    if test:
        return split_func(tple, int(len(x) * train_size))
    return split_func(tple, -1)