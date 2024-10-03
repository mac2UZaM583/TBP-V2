from sklearn.neighbors import KNeighborsClassifier

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

def g_knn_predict(
    x, 
    y, 
    x_test, 
    n_neighbors=3
):
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)
    knn.fit(x, y)
    return knn.predict(x_test)