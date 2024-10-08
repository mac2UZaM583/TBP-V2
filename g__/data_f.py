import pandas as pd
import numpy as np

def g_klines_splitting(klines):
    return pd.DataFrame({
        'close': klines[:, 4],
        'high': klines[:, 2],
        'low': klines[:, 3],
    })

def g_train_test_split(
    x, 
    y,
    test=False,
    train_size=0.8,
):  
    cutback = np.max([
        index 
        for column in x.columns 
        for index in x[column].index[x[column].isna()]
    ]) + 1
    x = x[cutback:]
    y = y[cutback:]
    split_func = lambda v, len_: [
        v[i][len_:] 
        if i % 2 != 0 
        else v[i][:len_]
        for i in range(4) 
    ]
    tple = (x, x, y, y)
    if test:
        return split_func(tple, int(len(x) * train_size))
    return split_func(tple, -1)

def g_df_create_replace(
    data, 
    columns, 
    range_, 
    replace,
):
    def g_df_fill(
        data, 
        columns, 
        value=np.nan
    ):
        for column in columns:
            data[column] = value
        return data
    
    data = g_df_fill(data, columns)
    for i in range(len(range_)):
        data.loc[range_[i], columns[i]] = replace[i]
    return data