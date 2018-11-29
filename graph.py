# %%

import numpy as np
from itertools import chain
from config import TWEETS_DIR, TWEETS_FILENAME, TEMP_DIR
import pickle as pkl
import os
from typing import Dict, Sequence

import pandas as pd
from tqdm import tqdm

from config import GROUPS, TEMP_DIR
from dataset.stats import *

try:
    import graph_tool.all as gt
except ImportError:
    print('Install graph-tool for python>3.5, please ;-;')
    exit(-1)


# %%

def create_graph(mentions: pd.DataFrame):
    graph_path = os.path.join(TEMP_DIR, 'graph.ml')
    graph_format = 'graphml'

    if os.path.isfile(graph_path):
        return gt.load_graph(graph_path, graph_format)

    graph = gt.Graph(directed=False)

    vp_username = graph.new_vp('string')
    vp_group = graph.new_vp('int')

    graph.vp.username = vp_username
    graph.vp.group = vp_group

    def get_vertex_and_create_if_not_exist(group: str, username: str):
        v = gt.find_vertex(graph, graph.vp.username, username)

        if not v:
            v = graph.add_vertex()
            graph.vp.group[v] = GROUPS.index(group)
            graph.vp.username[v] = username
            return v
        else:
            return v[0]

    for idx, (group, username, mentioned) in tqdm(mentions.iterrows(),
                                                  total=mentions.shape[0],
                                                  desc='Creating graph',
                                                  leave=False):
        username = get_vertex_and_create_if_not_exist(group, username)
        mentioned = get_vertex_and_create_if_not_exist(group, mentioned)
        e = graph.edge(username, mentioned, add_missing=False)
        if not e:
            graph.add_edge(username, mentioned, add_missing=False)

    print(f'Saving graph to {graph_path} (format: {graph_format})')
    graph.save(graph_path, graph_format)
    return graph


# print_stats()
# %%
g = create_graph(get_mentions(False))

# %%
layout = gt.sfdp_layout(g,
                        vweight=None,
                        eweight=None,
                        pin=None,
                        groups=None,
                        C=0.2,
                        K=None,
                        p=2.0,
                        theta=0.6,
                        max_level=15,
                        gamma=1.0,
                        mu=0.0,
                        mu_p=1.0,
                        init_step=None,
                        cooling_step=0.95,
                        adaptive_cooling=True, 
                        epsilon=0.01, 
                        max_iter=0, 
                        pos=None, 
                        multilevel=None, 
                        coarse_method='hybrid', 
                        mivs_thres=0.9, 
                        ec_thres=0.75, 
                        coarse_stack=None, 
                        weighted_coarse=False, 
                        verbose=False)
gt.graph_draw(g,
              pos=layout,
              vertex_fill_color=g.vp.group,
              output_size=(3840, 2160))
#   output=os.path.join(RESOURCE_DIR, 'graph.pdf'),
# gt.draw_hierarchy(g)


# %%
