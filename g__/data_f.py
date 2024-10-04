from sklearn.neighbors import KNeighborsClassifier
import numpy as np

def g_train_test_split(
    x, 
    y,
    test=False,
    train_size=0.8,
):  
    split_func = lambda v, len_: tuple(
        v[i][len_:] 
        if i % 2 != 0 
        else v[i][:len_]
        for i in range(4) 
    )
    tple = (x, x, y, y)
    if test:
        return split_func(tple, int(len(x) * train_size))
    return split_func(tple, -1)

def g_y(
    data, 
    feauture_main={"RSI": (70, 30)}, 
    feautures_add={}
):
    # rsi 70 30
    # tsi (0.8, 0.97, 0.87, 0.95, 0.8) 
    feautures_all = feauture_main | feautures_add
    
    if__ = zip(*[
        (
            data[feauture] > feautures_all[feauture][0],
            data[feauture] < feautures_all[feauture][1]
        )
        for feauture in feautures_all
    ])
    if feautures_add:
        if_sell, if_buy = [lambda v, arr: v[[np.all(v == arrv, axis=0) for arrv in arr]](el[0], el) for el in if__]
    else:
        if_sell, if_buy = [el[0] for el in if__]
    return np.where(if_sell, -1, np.where(if_buy, 1, 0))

def g_knn_predict(
    x, 
    y, 
    x_test, 
    n_neighbors=3
):
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)
    knn.fit(x, y)
    return knn.predict(x_test)