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