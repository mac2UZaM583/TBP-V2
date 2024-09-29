from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score
from sklearn.impute import SimpleImputer
import plotly.graph_objects as go
from pybit.unified_trading import HTTP
import time
import numpy as np
import pandas as pd
import asyncio
from pprint import pprint

session = HTTP()

async def g_klines(
    symbol, 
    qty,
    interval=1, 
):
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

def g_indications(
    klines,
    closed,
    rsi_args=(10, 14, 21, 31),
    tsi_args=(10, 14, 21),
    wt_args=((3, 7), (9, 14)), 
):
    # def g_lorentzian_distance(i, features_array, features_series):
    #     return np.sum([
    #         np.log(1 + np.abs(features_series[i_] - features_array[i_][i]))
    #         for i_ in range(len(features_series))
    #     ])
    
    def g_rsi(closed, period=14,):
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
    
    def g_tsi(closed, period=14,):
        return np.array([
            np.corrcoef(closed[i:i + period], np.arange(len(closed))[i:i + period])[0, 1]
            for i in range(len(closed) - period + 1)
        ])

    def g_wt(klines, periods=(10, 21),):
        def clclt_ema(prices, span=3):
            alpha = 2 / (span + 1)
            ema_values = []
            ema_values.append(prices[0])
            for price in prices[1:]:
                ema_values.append((price - ema_values[-1]) * alpha + ema_values[-1])
            return np.array(ema_values)
        
        prices_mean_ = (klines[:, 2] + klines[:, 3] + klines[:, 4]) / 3
        closes = klines[:, 4]
        emas_mean = [
            (closes + clclt_ema(prices_mean_, period)) / 2
            for period in periods
        ]
        wt_change = emas_mean[0] - emas_mean[1]
        wt_min = np.min(wt_change)
        return (wt_change - wt_min) / (np.max(wt_change) - wt_min) * 200 - 100

    def array_nan_func(data, len_=len(klines),):
        array_nan = np.full(len_, np.nan)
        array_nan[-len(data):] = data
        return array_nan

    funcs_results_func = lambda func, data, args: [func(data, arg) for arg in args]
    funcs_results = (
        *funcs_results_func(g_rsi, closed, rsi_args),
        *funcs_results_func(g_tsi, closed, tsi_args),
        *funcs_results_func(g_wt, klines, wt_args),
    )
    return tuple(map(lambda v: array_nan_func(v,), funcs_results))

def g_train_test_split(
    closed, 
    indications,
    test=False,
    train_size=0.8,
    profit_threshold=0.01,
    ftrs_nxt=10,
    ftrs_back=0,
):  
    x, y = [], []
    for i in range(ftrs_back, len(closed) - ftrs_nxt):
        changes = closed[i] / closed[i + ftrs_nxt]
        x_2l = [el[i] for el in indications]
        x.append(x_2l)
        if i == ftrs_back or y[i - ftrs_back - 1] == 0:
            y.append(
                -1 if changes >= 1 + profit_threshold
                else 1 if changes <= 1 - profit_threshold
                else 0
            )
        else:
            y.append(0)
    
    x = SimpleImputer(strategy="mean").fit_transform(x)
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

def g_knn_indicator(
    x, 
    y, 
    x_test, 
    n_neighbors=3
):
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)
    knn.fit(x, y)
    return knn.predict(x_test)

def g_presition_result(
    y_pred, 
    closed, 
    profit_threshold=0.01,
    ftrs_nxt=10, 
):
    lst = []
    for i in range(len(closed) - len(y_pred), len(closed) - ftrs_nxt):
        if y_pred[i - (len(closed) - len(y_pred))] != 0:
            changes = closed[i] / closed[i + ftrs_nxt]
            lst.append(
                y_pred[i - (len(closed) - len(y_pred))] == (
                    -1 if changes >= 1 + profit_threshold
                    else 1 if changes <= 1 - profit_threshold
                    else 0
                )
            )
    lst = np.array(lst)
    len_lst = len(lst)
    sum_lst = sum(lst)
    if len_lst == 0 or sum_lst == 0:
        return 0
    return round(sum_lst / len_lst * 100, 2)

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
    klines = np.float64(asyncio.run(g_klines("SUIUSDT", 10_000)))[::-1]
    closed = klines[:, 4]
    profit_threshold = 0.005
    ftrs_nxt = 10
    indications = g_indications(klines, closed)
    x, x_test, y, y_test = g_train_test_split(
        closed, 
        indications,
        test=True,
        train_size=0.8,
        ftrs_nxt=ftrs_nxt,
        profit_threshold=profit_threshold,
    )
    y_pred = g_knn_indicator(x, y, x_test, n_neighbors=3)
    # pprint(y_pred)
    # pprint(f"Точность предсказания: {g_presition_result(
    #     y_pred, 
    #     closed, 
    #     ftrs_nxt=ftrs_nxt,
    #     profit_threshold=profit_threshold,
    # )}%")
    g_visualize(
        np.arange(len(closed[len(closed) - len(y_pred):])),
        closed[len(closed) - len(y_pred):],
        y_pred,
        ftrs_nxt=ftrs_nxt,
        profit_threshold=profit_threshold,
    )

main()


# ^G/^F