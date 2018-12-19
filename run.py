#!/bin/python
#%%
import os
import pandas as pd

from dataset import merge_tweets_of_all_groups
from graph import create_graph, draw_graph, graph_measures

# merge_tweets_of_all_groups()
g = create_graph(only_classified_users=True, override=True)
meas = graph_measures(g)

features = pd.read_csv(os.path.join('dataset', 'twitter_patterns.csv'), header=0)
features.join(meas.set_index(['tp_group', 'tp_author']), on=['tp_group', 'tp_author']).fillna(0).to_csv('with_graph.csv', index=False)

# draw_graph(True)
