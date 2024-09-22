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
    ftrs_back=10,
):
    x, y = zip(*[
        (
            rsi[i - ftrs_back:i],
            -1 if closed[i] / closed[i + ftrs_back] >= 1 + profit_threshold 
            else 1 if closed[i] / closed[i + ftrs_back] <= 1 - profit_threshold 
            else 0
        )
        for i in range(ftrs_back, len(rsi) - ftrs_back)
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

def g_validate_model(
    y_pred, 
    closed, 
    profit_threshold=0.01,
    ftrs_nxt=10, 
):
    lst = []
    for i in range(len(closed) - ftrs_nxt):
        if y_pred[i] != 0:
            changes = closed[i] / closed[i + ftrs_nxt]
            lst.append(
                y_pred[i] == (
                    -1 if changes >= 1 + profit_threshold
                    else 1 if changes <= 1 - profit_threshold
                    else 0
                )
            )
    lst = np.array(lst)
    return round(sum(lst) / len(lst) * 100, 2)

def g_visualize(
    x_vis, 
    y_vis,
    target_y,
    ftrs_nxt=10,
    profit_threshold=0.01
):  
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vis, 
        y=y_vis, 
        mode='lines+markers', 
        name='Closed', 
        line=dict(color='blue')
    ))
    for i in range(len(x_vis) - ftrs_nxt):
        side = "buy" if target_y[i] == 1 else "sell" if target_y[i] == -1 else False
        if side:
            for i_ in range(2):
                x_ann = i
                y_ann = y_vis[i]
                text = side
                txt_color = 'green' if text == "buy" else 'red'
                color_border, borderwidth, borderpad = np.full(3, None)
                if i_:
                    x_ann = (i + ftrs_nxt)
                    y_ann = y_vis[i + ftrs_nxt]
                    text = "close"
                    txt_color = "black"
                    price_changes = y_vis[i] / y_vis[i + ftrs_nxt]
                    color_border = "green" if any((
                        price_changes >= 1 + profit_threshold and side == "sell",
                        price_changes <= 1 - profit_threshold and side == "buy"
                    )) else "red"
                    borderwidth = 3
                    borderpad = 1
                fig.add_annotation(
                    x=x_ann,  
                    y=y_ann + y_ann * 0.0015,
                    text=text, 
                    showarrow=True, 
                    arrowhead=2,
                    font=dict(size=12, color=txt_color),
                    bordercolor=color_border,
                    borderwidth=borderwidth,
                    borderpad=borderpad,
                )

            if i % 10 == 0:
                print(i, len(x_vis) - ftrs_nxt)

    fig.update_layout(
        title='График цен', 
        xaxis_title='Time', 
        yaxis_title='Price'
    )
    fig.show()

def main():
    closed, rsi = g_data("SUIUSDT", 10_000)
    ftrs_back = 40
    ftrs_nxt = 10
    profit_threshold_fr = 0.01
    profit_threshold = 0.01

    x, x_test, y, y_test, = g_pack_data(
        closed, 
        rsi, 
        test=True, 
        train_size=0.8, 
        profit_threshold=profit_threshold_fr, 
        ftrs_back=ftrs_back,
    )
    y_pred = g_knn_indicator(x, y, x_test)
    closed_stat = closed[len(closed) - len(y_pred) - ftrs_nxt:]
    print(f"PRESITION: {g_validate_model(
        y_pred, 
        closed_stat, 
        profit_threshold, 
        ftrs_nxt=ftrs_nxt,
    )}%")
    g_visualize(
        np.arange(len(closed_stat)), 
        closed_stat,
        y_pred,
        profit_threshold=profit_threshold,
        ftrs_nxt=ftrs_nxt,
    )

main()

