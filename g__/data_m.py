import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

def g_rsi(data, period=14):
    delta = data['close'].diff()
    return 100 - (100 / (
        1
        +
        delta
            .where(delta > 0, 0)
            .rolling(window=period)
            .mean()\
        / 
        (-delta.where(delta < 0, 0))
            .rolling(window=period)
            .mean()
    ))

def g_adx(
    high, 
    low, 
    close, 
    period=14
):
    atr = pd.DataFrame({
        'tr1': high - low, 
        'tr2': np.abs(high - close.shift()), 
        'tr3': np.abs(low - close.shift())
    })\
        .max(axis=1)\
        .rolling(window=period)\
        .mean()
    high_diff = high.diff()
    low_diff = low.diff()
    plus_di = 100 * (pd.Series(np.where(
        (high_diff > low_diff) & (high_diff > 0), 
        high_diff, 
        0
    ))\
        .rolling(window=period)\
        .mean() / atr)
    minus_di = 100 * (pd.Series(np.where(
        (low_diff > high_diff) & (low_diff > 0), 
        low_diff, 
        0
    ))\
        .rolling(window=period)\
        .mean() / atr)
    return (100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di)))\
        .rolling(window=period)\
        .mean()

def g_cci(data, period=20):
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    sma = typical_price.rolling(window=period).mean()
    return (typical_price - sma) / (0.015 * (typical_price - sma)\
        .abs()\
        .rolling(window=period)\
        .mean())

def g_williams_r(
    high, 
    low, 
    close, 
    period=14
):
    highest_high = high.rolling(window=period).max()
    return -100 * (highest_high - close) / (highest_high - low.rolling(window=period).min())

def g_tsi(closed, period=14,):
    return closed\
        .rolling(window=period)\
        .corr(pd.Series(np.arange(len(closed))))\
        .to_numpy()
    
def g_lorentzian_distances(feature_arrs, max_klines_back=500,):
    return np.sum([
        feature_arr\
            .rolling(window=max_klines_back)\
            .apply(lambda v: np.log(1 + np.abs(v.iloc[0] - v.iloc[-1])))
        for feature_arr in feature_arrs
    ], axis=0)

def g_indicators_data(
    klines, 
    need_indicators_l1=["RSI", "ADX", "CCI", "WT", "TSI"], 
    need_indicators_l2=["LD",]
):
    data = pd.DataFrame({
        'close': klines[:, 4],
        'high': klines[:, 2],
        'low': klines[:, 3],
    })
    choise_l1 = {
        "RSI": lambda: g_rsi(data),
        "ADX": lambda: g_adx(data['high'], data['low'], data['close']),
        "CCI":lambda: g_cci(data),
        "WT": lambda: g_williams_r(data['high'], data['low'], data['close']),
        "TSI": lambda: g_tsi(data["close"])
    }
    choise_l2 = {
        "LD": lambda: g_lorentzian_distances([data[el] for el in need_indicators_l1])
    }
    for el in need_indicators_l1:
        data[el] = choise_l1[el]()
    for el in need_indicators_l2:
        data[el] = choise_l2[el]()
    return data\
        .apply(lambda v: v.fillna(v.mean()))\
        [need_indicators_l1 + need_indicators_l2 + ["close", "high", "low",]]

def g_y(
    data, 
    feauture_main={"name": "RSI", "sell": 70, "buy": 30}, 
    features_add={}
):
    # rsi 70 30
    # tsi (0.8, 0.97, 0.87, 0.95, 0.8) 
    
    main_sell = data[feauture_main["name"]] > feauture_main["sell"]
    main_buy =  data[feauture_main["name"]] < feauture_main["buy"]
    
    if features_add:
        additional_conditions = [
            (data[feature] > thresholds[0], data[feature] < thresholds[1])
            for feature, thresholds in features_add.items()
        ]
        cond_1, cond_2 = zip(*[
            [*cond]
            for cond in additional_conditions
        ])
        main_sell = np.logical_and(main_sell, np.all(cond_1, axis=0))
        main_buy = np.logical_and(main_buy, np.all(cond_2, axis=0))
    return np.where(main_sell, -1, np.where(main_buy, 1, 0))

def g_knn_predict(
    x, 
    y, 
    x_test, 
    n_neighbors=3
):
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)
    knn.fit(x, y)
    return knn.predict(x_test)