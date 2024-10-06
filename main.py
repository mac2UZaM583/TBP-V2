from g__.data_ import g_klines
from g__.data_m import (
    g_indicators_data,
    g_knn_predict,
    g_y,
)
from g__.data_f import g_train_test_split
from vis import g_visualize

import numpy as np
from sklearn.metrics import classification_report

def main():
    in_need_l1 = {
        "RSI": dict(period=14,), 
        "ADX": dict(period=14,), 
        "CCI": dict(period=21,), 
        "WT": dict(period=14,), 
        "TSI": dict(period=14,),
    }
    in_need_l2 = {"LD": dict(bars_back=500,)}
    data = g_indicators_data(
        np.float64(g_klines("SUIUSDT", 2_000)), 
        in_need_l1=in_need_l1,
        in_need_l2=in_need_l2,
    )
    # print(data["TSI"])
    # print(data["RSI"][-10:])
    # x_train, x_test, y_train, y_test = g_train_test_split(
    #     data[need_indicators_l1 + need_indicators_l2], 
    #     g_y(data), 
    #     test=True
    # )
    # y_pred = g_knn_predict(x_train, y_train, x_test) 
    # data['Predicted Label'] = np.nan 
    # data["train_label"] = np.nan
    # data.loc[x_test.index, 'Predicted Label'] = y_pred 
    # data.loc[x_train.index, "train_label"] = y_train
    # print(classification_report(y_test, y_pred))

    g_visualize(
        x=data.index,
        y=data["RSI"]
    )
    # g_visualize(
    #     x=data.index,
    #     y=data["close"],
    #     markers=(
    #         dict(
    #             data=data[data['train_label'] == -1],
    #             color='red',
    #             name='Sell'
    #         ),
    #         dict(
    #             data=data[data['train_label'] == 1],
    #             color='green',
    #             name='Buy'
    #         )
    #     )
    # )
# while True:
main()

# визуализировать все на графике и рядом с графиком 