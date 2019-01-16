#!/bin/python
import pickle
import subprocess as sp
from itertools import product

import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score
from tqdm import tqdm
import os
DIR_MODELS = 'models'

if not os.path.isdir(DIR_MODELS):
    os.mkdir(DIR_MODELS)


def wc(filename):
    return int(sp.check_output(['wc', '-l', filename]).split()[0])


def save_to_pickle(obj, filepath: str):
    with open(filepath + '.pkl', 'wb') as f:
        pickle.dump(obj, f)


def load_from_pickle(filepath: str):
    with open(filepath, 'rb') as f:
        return pickle.load(f, fix_imports=True)


def save_to_csv(obj, filepath: str):
    with open(filepath + '.csv', 'w') as f:
        for line in tqdm(obj, 'saving to ' + filepath):
            f.writelines(','.join(list(map(str, line))) + '\n')


def krzys_save_to_csv(x, y, filepath: str):
    with open('krzyz_' + filepath + '.csv', 'w') as f:
        for x, y in tqdm(zip(x, y), 'krzysiowanie', len(x)):
            f.writelines(','.join(list(map(str, x))) + ',' + y + '\n')


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


def load_base():
    dataset_filepath = 'feat_glob_avg_dataset.txt'
    with open(dataset_filepath, 'r') as f:
        for line in tqdm(f, 'lines', wc(dataset_filepath)):
            feat_class = line.split(',')
            x = list(map(float, feat_class[:200]))
            y = feat_class[200].replace('\n', '')
            X.append(x), Y.append(y)
    return X, Y

def score(Y_test, preds):
    acc = accuracy_score(Y_test, preds)
    f1 = f1_score(Y_test, preds, average='macro')
    prec = precision_score(Y_test, preds, average='macro')
    rec = recall_score(Y_test, preds, average='macro')
    return acc, f1, prec, rec

def print_scores(acc, f1, prec, rec):
    print('acc', acc)
    print('f1', f1)
    print('prec', prec)
    print('rec', rec)

# X, Y = load_base()
# X, X_test, Y, y_test = train_test_split(X, Y, test_size=0.20, random_state=42)
# krzys_save_to_csv(X, Y, 'train')
# krzys_save_to_csv(X_test, y_test, 'test')


X, Y = load_from_csv('krzyz_train')
X_test, Y_test = load_from_csv('krzyz_test')

results = [['n_estimators', 'max_depth', 'accuracy', 'f1', 'precision', 'recall']]
for n_estimators, max_depth in product([30, ], [20, ]):
    clf = RandomForestClassifier(n_estimators=n_estimators,
                                 max_depth=max_depth,
                                 n_jobs=8,
                                 min_samples_leaf=1,
                                 random_state=64,
                                 verbose=10)
                                 
    clf.fit(X, Y)
    preds = clf.predict(X_test)

    scores = score(Y_test, preds)
    results.append([n_estimators, max_depth, *scores])
    print_scores(*scores)

    save_to_pickle(clf, os.path.join(DIR_MODELS, '{}_{}'.format(n_estimators, max_depth)))

save_to_csv(results, 'results')
