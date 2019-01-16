#!/bin/python
#%%
import os
import pandas as pd

from dataset import merge_tweets_of_all_groups
from graph import create_graph, graph_measures, merge_graph_feats_with_tweet_feats, draw_graph

# merge_tweets_of_all_groups()

g = create_graph(only_classified_users=True, override=True)
# meas = graph_measures(g)
# merge_graph_feats_with_tweet_feats(meas)

draw_graph(False)
