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
        g_y_train(
            data, 
            feauture_main={"name": "RSI", "sell": 70, "buy": 30},
            features_add={"ADX": (20, 40, True)}
        ),
        test=True,
    )
    data = g_df_replace(
        data=data,
        columns=["train_label", "predicted_label"],
        indeces=(x_train.index, x_test.index),
        replace=(y_train, g_knn_predict(x_train, x_test, y_train,))
    )
    g_visualize(
        x=data.index,
        y=data["close"],
        markers_target=data["train_label"],
        markers_settings=(
            dict(
                class_=-1,
                color='red',
                name='Sell'
            ),
            dict(
                class_=1,
                color='green',
                name='Buy'
            )
        )
    )

main()

# отобразить на графике индкаторы и составить наилучшие значения
# визуализировать все на графике и рядом с графиком 