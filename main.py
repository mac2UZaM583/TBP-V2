from g__.data_ import *
from g__.data_m import *
from g__.data_f import *
from vis import *

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

def main():
    data = g_indicators_data(
        g_klines_splitting(np.float64(g_klines("SUIUSDT", 3_000))),
        in_need_l1={
            "RSI": dict(period=14,), 
            "ADX": dict(period=14,), 
            "CCI": dict(period=21,), 
            "WT": dict(period=14,), 
            "TSI": dict(period=14,),
        },
        in_need_l2={"LD": dict(bars_back=500,)},
    )
    x_train, x_test, y_train, y_test = g_train_test_split(
        data[[column for column in data.columns if "INDCS/ " in column]], 
        g_y_train(data), 
        test=True,
    )
    data = g_df_fill(data, ["predicted_label", "train_label"])
    data.loc[x_test.index, 'predicted_label'] = g_knn_predict(x_train, x_test, y_train,) 
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

main()

# визуализировать все на графике и рядом с графиком 