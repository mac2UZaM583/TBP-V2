import pandas as pd
import numpy as np

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

def g_lorentzian_distance_s(feature_arrays, len_data):
    g_lorentzian_distance = lambda v_1, v_2: np.log(1 + np.abs(v_1 - v_2))
    return [
        g_lorentzian_distance(feature_arrays["f1"][i], feature_arrays["f2"][i]) + \
        g_lorentzian_distance(feature_arrays['f3'][i], feature_arrays['f4'][i])
        for i in range(len_data)
    ]