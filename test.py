from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score
import plotly.graph_objects as go
from pybit.unified_trading import HTTP
import time
import numpy as np
import asyncio
from pprint import pprint

session = HTTP()


def g_data(symbol="ATOMUSDT", qty=10_000):
    async def g_klines(interval, qty):
        start = time.time() * 1000
        limits = np.append(np.full(qty // 1000, 1000), qty % 1000)
        return np.concatenate(await asyncio.gather(*(
            asyncio.to_thread(lambda i=i: session.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limits[i],
                end=str(int(start - (i * 60_000_000)))
            )["result"]["list"])
            for i in range(len(limits))
            if limits[i] > 0
        )))

    def g_rsi(closed, period=14):
        changes = np.diff(closed)
        gains = np.where(changes > 0, changes, 0)
        losses = -np.where(changes < 0, changes, 0)
        avg_gain = np.mean(gains[:period])
        avg_losses = np.mean(losses[:period])
        
        rsi = []
        for i in range(period, len(changes) + 1):
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_losses = (avg_losses * (period - 1) + losses[i - 1]) / period
            rsi.append(100 - (100 / (1 + avg_gain / avg_losses)))
        return np.array(rsi)
    
    closed = np.float64(asyncio.run(g_klines(1, qty))[:, 4][::-1])
    return (closed[14:], g_rsi(closed))

def g_pack_data(
    closed, 
    rsi,
    test=False,
    train_size=0.8,
    profit_threshold=0.01,
    features=10,
):
    x, y = zip(*[
        (
            rsi[i - features:i],
            # на основе текущего rsi даем классы основываясь на будущем изменении цены
            -1 if closed[i] / closed[i + features] >= 1 + profit_threshold 
            else 1 if closed[i] / closed[i + features] <= 1 - profit_threshold 
            else 0
        )
        for i in range(features, len(rsi) - features)
    ])
    if test:
        len_80 = int(len(x) * train_size)
        return (
            np.array(x)[:len_80],
            np.array(x)[len_80:],
            np.array(y)[:len_80],
            np.array(y)[len_80:],
        )
    return (
        np.array(x)[:-1], 
        np.array(x)[-1], 
        np.array(y)[:-1],
        np.array(y)[-1],
    )

def g_knn_indicator(x, y, x_test):
    knn = KNeighborsClassifier(n_neighbors=3)
    knn.fit(x, y)
    return knn.predict(x_test)

def g_visualize(
    x_visualize, 
    y_visualize,
    target_y,
    features=10,
):  
    len_x_vis_us = len(x_visualize) -features
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_visualize, 
        y=y_visualize, 
        mode='lines+markers', 
        name='Closed', 
        line=dict(color='blue')
    ))
    for i in range(len_x_vis_us):
        text = "buy" if target_y[i] == 1 else "sell" if target_y[i] == -1 else False
        if text:
            print(i, len_x_vis_us)
            fig.add_annotation(
                x=i, 
                y=y_visualize[i] + y_visualize[i] * 0.0015,
                text=text, 
                showarrow=True, 
                arrowhead=2,
                font=dict(size=12, color='green' if text == "buy" else 'red'),
            )
            fig.add_annotation(
                x=i + features, 
                y=y_visualize[i + features] + y_visualize[i + features] * 0.0015,
                text="close", 
                showarrow=True, 
                arrowhead=2
            )

    fig.update_layout(
        title='График цен', 
        xaxis_title='Time', 
        yaxis_title='Price'
    )
    fig.show()

def g_validate_model(
    y_pred, 
    closed, 
    features=10, 
    profit_threshold=0.01
):
    len_closed = len(closed)
    len_y = len(y_pred)
    lst = [
        y_pred[i - (len_closed - len_y)] == (-1
        if closed[i] / closed[i + features] >= 1 + profit_threshold
        else 1 if closed[i] / closed[i + features] <= 1 - profit_threshold 
        else 0)
        for i in range(len_closed - len_y, len_closed - features)
    ]
    return round(sum(lst) / len(lst) * 100, 2)

def main():
    closed, rsi = g_data("CETUSUSDT", 2000)
    features = 10
    x, x_test, y, y_test, = g_pack_data(closed, rsi, test=True, train_size=0.7)
    y_pred = g_knn_indicator(x, y, x_test)
    
    print(f"PRESITION: {g_validate_model(y_pred, closed)}%")
    closed_vis = closed[len(closed) - len(y_pred) - features:]
    g_visualize(
        np.arange(len(closed_vis)), 
        closed_vis,
        y_pred,
    )

main()

