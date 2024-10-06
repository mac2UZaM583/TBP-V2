from g__.data_ import *
from g__.data_m import *
from g__.data_f import *
from vis import *

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

def main():
    # reuse
    cutback = 500
    in_need_l1 = {
        "RSI": dict(period=14,), 
        "ADX": dict(period=14,), 
        "CCI": dict(period=21,), 
        "WT": dict(period=14,), 
        "TSI": dict(period=14,),
    }
    in_need_l2 = {"LD": dict(bars_back=cutback,)}
    
    data = g_indicators_data(
        g_klines_splitting(np.float64(g_klines("SUIUSDT", 3_000))),
        in_need_l1=in_need_l1,
        in_need_l2=in_need_l2,
    )
    x_train, x_test, y_train, y_test = g_train_test_split(
        data[list(in_need_l1.keys()) + list(in_need_l2.keys())], 
        g_y_train(data), 
        test=True,
        cutback=cutback,
    )
    y_pred = g_knn_predict(x_train, y_train, x_test) 
    data['Predicted Label'] = np.nan 
    data["train_label"] = np.nan
    data.loc[x_test.index, 'Predicted Label'] = y_pred 
    data.loc[x_train.index, "train_label"] = y_train
    g_visualize(
        x=data.index,
        y=data["close"],
        markers=(
            dict(
                data=data[data['train_label'] == -1],
                color='red',
                name='Sell'
            ),
            dict(
                data=data[data['train_label'] == 1],
                color='green',
                name='Buy'
            )
        )
    )
# while True:
main()

# визуализировать все на графике и рядом с графиком 