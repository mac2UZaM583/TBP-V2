import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

def g_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

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
    }).max(axis=1).rolling(window=period).mean()
    high_diff = high.diff()
    low_diff = low.diff()
    plus_di = 100 * (pd.Series(np.where(
        (high_diff > low_diff) & (high_diff > 0), 
        high_diff, 
        0
    )).rolling(window=period).mean() / atr)
    minus_di = 100 * (pd.Series(np.where(
        (low_diff > high_diff) & (low_diff > 0), 
        low_diff, 
        0
    )).rolling(window=period).mean() / atr)

    dx = 100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di))
    return dx.rolling(window=period).mean()

def g_cci(data, period=20):
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    sma = typical_price.rolling(window=period).mean()
    mean_deviation = (typical_price - sma).abs().rolling(window=period).mean()
    return (typical_price - sma) / (0.015 * mean_deviation)

def g_williams_r(
    high, 
    low, 
    close, 
    period=14
):
    highest_high = high.rolling(window=period).max()
    return -100 * (highest_high - close) / (highest_high - low.rolling(window=period).min())

def g_lorentzian_distances(feature_arrays, len_data):
    g_lorentzian_distance = lambda v_1, v_2: np.log(1 + np.abs(v_1 - v_2))
    return [
        np.sum(g_lorentzian_distance(
            feature_arrays[i_][i], feature_arrays[i_ + 1][i]) 
            for i_ in range(0, len(feature_arrays), 2)
        )
        for i in range(len_data)
    ]

def g_indicators_data(
    klines, 
    need_indicators_l1=["RSI", "ADX", "CCI", "WT",], 
    need_indicators_l2=["LD",]
):
    data = pd.DataFrame({
        'close': klines[:, 4],
        'high': klines[:, 2],
        'low': klines[:, 3],
    })
    choise = {
        "RSI": lambda: g_rsi(data),
        "ADX": lambda: g_adx(data['high'], data['low'], data['close']),
        "CCI":lambda: g_cci(data),
        "WT": lambda: g_williams_r(data['high'], data['low'], data['close']),
    }
    for el in need_indicators_l1:
        data[el] = choise[el]()
    for el in need_indicators_l2:
        data[el] = g_lorentzian_distances([data[el].values for el in need_indicators_l1], len(data))
    return data.apply(lambda v: v.fillna(v.mean()))[need_indicators_l1 + need_indicators_l2 + ["close", "high", "low",]]

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
        main_sell = np.logical_and(main_sell, np.all([cond[0] for cond in additional_conditions], axis=0))
        main_buy = np.logical_and(main_buy, np.all([cond[1] for cond in additional_conditions], axis=0))
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