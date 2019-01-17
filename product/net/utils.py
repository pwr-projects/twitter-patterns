from itertools import product

import matplotlib.pyplot as plt
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
import numpy as np


def print_scores(acc, f1, prec, rec):
    print('acc', acc)
    print('f1', f1)
    print('prec', prec)
    print('rec', rec)


def score(Y_test, preds):
    acc = accuracy_score(Y_test, preds)
    f1 = f1_score(Y_test, preds, average='macro')
    prec = precision_score(Y_test, preds, average='macro')
    rec = recall_score(Y_test, preds, average='macro')
    return acc, f1, prec, rec


def plot_confusion_matrix(y_true, y_pred, classes):
    cm = confusion_matrix(y_true, y_pred)
    cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Confusion matrix')
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f'
    thresh = cm.max() / 2.
    for i, j in product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.show()
