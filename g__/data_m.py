import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

def g_rsi(data, period=14):
    delta = data['close'].diff()
    return 100 - (100 / (
        1
        +
        (delta.where(delta > 0, 0))
            .rolling(window=period)
            .mean()
        / 
        (-delta.where(delta < 0, 0))
            .rolling(window=period)
            .mean()
            .replace(0, np.nan)
    ))

def g_adx(data, period=14):
    atr = pd.DataFrame({
        'tr1': data["high"] - data["low"], 
        'tr2': np.abs(data["high"] - data["close"].shift()), 
        'tr3': np.abs(data["low"] - data["close"].shift())
    })\
        .max(axis=1)\
        .rolling(window=period)\
        .mean()
    low_diff, high_diff = map(lambda v: v.diff(), (data["low"], data["high"]))
    calculate_di = lambda v1, v2: 100 * (
        pd.Series(np.where((v1 > v2) & (v1 > 0), v1, 0))
            .rolling(window=period)
            .mean()
        / atr
    )
    minus_di = calculate_di(low_diff, high_diff)
    plus_di = calculate_di(high_diff, low_diff)

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

def g_williams_r(data, period=14):
    highest_high = data["high"].rolling(window=period).max()
    return -100 * (highest_high - data["close"]) / (
        highest_high - 
        data["low"]
            .rolling(window=period)
            .min()
    )

def g_tsi(data, period=14,):
    return data["close"]\
        .rolling(window=period)\
        .corr(pd.Series(np.arange(len(data["close"]))))\
    
def g_lorentzian_distances(feature_arrs, bars_back=500,):
    return np.sum([
        feature_arr\
            .rolling(window=bars_back)\
            .apply(lambda v: np.log(1 + np.abs(v.iloc[0] - v.iloc[-1])))
        for feature_arr in feature_arrs
    ], axis=0)

def g_indicators_data(
    data, 
    in_need_l1={
        "RSI": dict(period=14,), 
        "ADX": dict(period=14,), 
        "CCI": dict(period=21,), 
        "WT": dict(period=14,), 
        "TSI": dict(period=14,),
    }, 
    in_need_l2={"LD": dict(bars_back=500,)}
):
    choise_l1 = {
        "RSI": lambda: g_rsi(data, **in_need_l1["RSI"]),
        "ADX": lambda: g_adx(data, **in_need_l1["ADX"]),
        "CCI":lambda: g_cci(data, **in_need_l1["CCI"]),
        "WT": lambda: g_williams_r(data, **in_need_l1["WT"]),
        "TSI": lambda: g_tsi(data, **in_need_l1["TSI"])
    }
    choise_l2 = {
        "LD": lambda v: g_lorentzian_distances(v)
    }
    for el in in_need_l1:
        data[el] = choise_l1[el]()
    l1 = [data[el] for el in in_need_l1]
    for el in in_need_l2:
        data[el] = choise_l2[el](l1)
    return data.rename(columns={
        name: "INDCS/ " + name
        for name in list(in_need_l1.keys()) + list(in_need_l2.keys())
    })

def g_y_train(
    data, 
    feauture_main={"name": "RSI", "sell": 70, "buy": 30}, 
    features_add={}
):
    # rsi 70 30
    # tsi (0.8, 0.97, 0.87, 0.95, 0.8) 
    
    feauture_main["name"] = "INDCS/ " + feauture_main["name"]
    for i in range(len(features_add)):
        key_ = list(features_add.keys())[i]
        features_add["INDCS/ " + key_] = features_add.pop(key_)
    main_sell = data[feauture_main["name"]] > feauture_main["sell"]
    main_buy =  data[feauture_main["name"]] < feauture_main["buy"]
    
    if features_add:
        invert_func = lambda v, bool_: np.invert(v) if bool_ else v
        main_sell, main_buy = [
            np.logical_and(side, np.all(cond, axis=0)) 
            for side, cond in zip(
                (main_sell, main_buy), 
                zip(*[[*cond] for cond in [
                    invert_func((
                        (data[feature] > thresholds[0]), 
                        ((data[feature] < thresholds[1]) if thresholds[1] != None else (data[feature] > thresholds[0])) 
                    ), thresholds[2])
                    for feature, thresholds in features_add.items()
                ]])
            )
        ]
    return pd.Series(np.where(main_sell, -1, np.where(main_buy, 1, 0)))

def g_df_replace(
    data, 
    columns, 
    indeces, 
    replace,
):
    def g_df_fill(
        data, 
        columns, 
        value=np.nan
    ):
        for column in columns:
            data[column] = value
        return data
    
    data = g_df_fill(data, columns)
    for i in range(len(indeces)):
        data.loc[indeces[i], columns[i]] = replace[i]
    return data

def g_knn_predict(
    x_train, 
    x_test, 
    y_train, 
    n_neighbors=3
):
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)
    knn.fit(x_train, y_train)
    return knn.predict(x_test)