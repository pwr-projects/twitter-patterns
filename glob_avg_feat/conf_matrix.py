
import itertools
import pickle
import subprocess as sp

import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, svm
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def wc(filename):
    return int(sp.check_output(['wc', '-l', filename]).split()[0])


def load_from_pickle(filepath: str):
    with open(filepath, 'rb') as f:
        return pickle.load(f, fix_imports=True)


def plot_confusion_matrix(cm,
                          classes,
                          normalize=True,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.show()


def load_from_csv(filepath: str):
    X, Y = [], []
    filepath += '.csv'
    with open(filepath, 'r') as f:
        for line in tqdm(f, filepath, wc(filepath)):
            feat_class = line.split(',')
            x = list(map(float, feat_class[:200]))
            y = feat_class[200].replace('\n', '')
            X.append(x), Y.append(y)
    return X, Y


X_test, Y_test = load_from_csv('krzyz_test')
clf = load_from_pickle('models/70_50.pkl')

preds = clf.predict(X_test)
cnf_matrix = confusion_matrix(Y_test, preds)
plot_confusion_matrix(cnf_matrix, clf.classes_)
