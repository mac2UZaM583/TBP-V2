from g__.data_ import g_klines
from g__.indicators import g_indicators_data
from g__.data_f import (
    g_train_test_split, 
    g_knn_predict,
    g_y,
)
from vis import g_visualize

import numpy as np
from sklearn.metrics import classification_report

def main():
    need_indicators_l1 = ['RSI', 'ADX', 'CCI', 'WT',]
    need_indicators_l2 = ['LD',]
    data = g_indicators_data(
        np.float64(g_klines("SUIUSDT", 2_000)), 
        need_indicators_l1=need_indicators_l1,
        need_indicators_l2=need_indicators_l2,
    )
    x_train, x_test, y_train, y_test = g_train_test_split(
        data[need_indicators_l1 + need_indicators_l2], 
        g_y(data), 
        test=True
    )
    y_pred = g_knn_predict(x_train, y_train, x_test) 
    data['Predicted Label'] = np.nan 
    data.loc[x_test.index, 'Predicted Label'] = y_pred 
    print(classification_report(y_test, y_pred))

    g_visualize(
        x=data.index,
        y=data["close"],
        markers=(
            dict(
                data=data[data['Predicted Label'] == -1],
                color='red',
                name='Sell'
            ),
            dict(
                data=data[data['Predicted Label'] == 1],
                color='green',
                name='Buy'
            )
        )
    )

main()

# визуализировать все на графике и рядом с графиком 