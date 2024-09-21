from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import plotly.graph_objects as go
from pybit.unified_trading import HTTP
import time
import numpy as np
import asyncio
from pprint import pprint

session = HTTP()


def g_data(
    symbol="LISTAUSDT",
    features=10,
    level_limit=10,
    profit_threshold=0.01,
    test_size=0.2,
):
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
    
    closed = np.float64(asyncio.run(g_klines(1, 10_000))[:, 4][::-1])
    rsi, closed = g_rsi(closed), closed[14:]
    x, y = zip(*[
        (
            rsi[i - features:i],
            -1 if closed[i - features] / closed[i] >= 1 + profit_threshold 
            else 1 if closed[i - features] / closed[i] <= 1 - profit_threshold 
            else 0
        )
        for i in range(features, len(rsi))
    ])
    len_80 = int(len(x) * 0.8)
    return (
        np.array(x[:len_80]),
        np.array(x[len_80:]),
        np.array(y[:len_80]),
        np.array(y[len_80:]),
        closed
    )

def main():
    x, x_test, y, y_test, closed = g_data()
    knn = KNeighborsClassifier(n_neighbors=3)
    knn.fit(x, y)
    y_pred = knn.predict(x_test)
    print(classification_report(y_test, y_pred))

    # from itertools import count
    # counter = count()
    # for y__ in y:
    #     if y__ == 1:
    #         print(next(counter))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=np.arange(len(closed)), 
        y=closed, 
        mode='lines+markers', 
        name='Closed', 
        line=dict(color='blue')
    ))
    target_y = y_pred
    for i in range(len(target_y)):
        text = "buy" if target_y[i] == 1 else "sell" if target_y[i] == -1 else False
        if text:
            print(i, len(target_y))
            fig.add_annotation(
                x=len(closed) - len(target_y) + i - 10, 
                y=closed[len(closed) - len(target_y) + i - 10] + 0.001,
                text=text, 
                showarrow=True, 
                arrowhead=2
            )
            fig.add_annotation(
                x=len(closed) - len(target_y) + i + 10 - 10, 
                y=closed[len(closed) - len(target_y) + i + 10 - 10] + 0.001,
                text="close", 
                showarrow=True, 
                arrowhead=2
            )

    fig.update_layout(title='График цен', xaxis_title='Time', yaxis_title='Price')
    fig.show()
main()
