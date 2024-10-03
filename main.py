import numpy as np
import pandas as pd
from data_ import g_klines
from format_data import *
from model_ import g_knn_predict
from sklearn.metrics import classification_report, accuracy_score
from test import g_visualize

def main():
    data = g_pack_data(np.float64(g_klines("SUIUSDT", 2_000)))
    x_train, x_test, y_train, y_test = g_train_test_split(
        data[['RSI', 'ADX', 'CCI', 'WT']], 
        np.where(data['RSI'] > 70, -1, np.where(data['RSI'] < 30, 1, 0)), 
        test=True
    )
    y_pred = g_knn_predict(x_train, y_train, x_test) 
    data['Predicted Label'] = np.nan 
    data.loc[x_test.index, 'Predicted Label'] = y_pred 
    print("Accuracy:", accuracy_score(y_test, y_pred))
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