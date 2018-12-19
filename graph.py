# %%
import os
import pickle as pkl
from itertools import chain, product
from os.path import join as pj
from typing import Dict, Sequence

import numpy as np
import pandas as pd
from tqdm import tqdm

from config import (GROUPS, RESOURCE_DIR, TEMP_DIR, TWEETS_DIR,
                    TWEETS_FILENAME, FEATURES_DIR, FEATURES_FILENAME,
                    FEATURES_INC_GRAPH_FILENAME, only_classified_users_str)
from dataset import get_mentions, get_mentions_path, wc

try:
    import graph_tool.all as gt
except ImportError:
    print('Install graph-tool for python>3.5, please ;-;')
    exit(-1)


# %%

def create_graph(only_classified_users: bool, override: bool = False):
    only_for_classified = only_classified_users_str(only_classified_users)
    graph_path = pj(TEMP_DIR, f'graph_{only_for_classified}.ml')
    graph_format = 'graphml'

    if not override and os.path.isfile(graph_path):
        return gt.load_graph(graph_path, graph_format)

    graph = gt.Graph(directed=True)

    vp_group_name = graph.new_vp('string')
    vp_group = graph.new_vp('int')
    vp_username = graph.new_vp('string')
    ep_weight = graph.new_ep('int')

    graph.vp.group_name = vp_group_name
    graph.vp.group = vp_group
    graph.vp.username = vp_username
    graph.ep.weight = ep_weight

    def get_vertex_and_create_if_not_exist(group_name: str, username: str):
        v = gt.find_vertex(graph, graph.vp.username, username)

        if not v:
            v = graph.add_vertex()
            graph.vp.group[v] = GROUPS.index(group_name)
            graph.vp.group_name[v] = group_name
            graph.vp.username[v] = username
            return v
        else:
            return v[0]

    def add_vartices_and_edges(group, username, mentioned):
        username = get_vertex_and_create_if_not_exist(group, username)
        mentioned = get_vertex_and_create_if_not_exist(group, mentioned)

        e = graph.edge(username, mentioned, add_missing=False)
        if not e:
            e = graph.add_edge(username, mentioned, add_missing=False)
        graph.ep.weight[e] += 1

    all_mentions_path = get_mentions_path(only_classified_users)

    if not os.path.exists(all_mentions_path):
        get_mentions(only_classified_users)

    for data in tqdm(pd.read_csv(all_mentions_path, header=0, chunksize=500),
                     total=int((wc(all_mentions_path) - 1) / 500),
                     desc='Creating graph',
                     leave=False):
        [add_vartices_and_edges(row.group, row.username, row.mentioned)
         for row in data.itertuples()]

    print(f'Saving graph to {graph_path} (format: {graph_format})')
    graph.save(graph_path, graph_format)
    return graph


def draw_graph(only_classified_users):
    g = create_graph(only_classified_users, False)

    pos = gt.sfdp_layout(g,
                         vweight=g.degree_property_map('total'),
                         eweight=g.ep.weight,
                         groups=g.vp.group,
                         multilevel=True,
                         gamma=1.0,
                         mu_p=0.2,
                         weighted_coarse=True,
                         coarse_method="hybrid",  # mivs hybrid ec
                         )
    return gt.graph_draw(g,
                         pos=pos,
                         vertex_fill_color=g.vp.group,
                         vertex_size=gt.prop_to_size(g.degree_property_map('total'), ma=20, mi=3),
                         edge_color='white',
                         edge_pen_width=0.1,
                         bg_color=[0.0, 0.0, 0.0, 1.0],
                         output_size=[800, 600],
                         # vertex_text=g.vp.username,
                         # vertex_font_size=8,
                         display_props=[g.vp.group_name, g.vp.username]
                         #   output=pj(RESOURCE_DIR, 'graph.pdf'),
                         )


def graph_measures(graph: gt.Graph) -> pd.DataFrame:
    def get_attrs(attrs): return (attrs[1][0], attrs[1][1][1], attrs[0])

    def append_val(key, prop, v): measures[key][0].append(prop[v])

    _, vp_authority, vp_hub = gt.hits(graph)

    measures = {key: ([], prop) for key, prop in {'tp_group': graph.vp.group_name,
                                                  'tp_author': graph.vp.username,
                                                  'tn_degree_in': graph.degree_property_map('in'),
                                                  'tn_degree_out': graph.degree_property_map('out'),
                                                  'tn_degree_total': graph.degree_property_map('total'),
                                                  'tn_pagerank': gt.pagerank(graph),
                                                  'tn_betweenness': gt.betweenness(graph)[0],
                                                  'tn_closeness': gt.closeness(graph),
                                                  'tn_eigenvector': gt.eigenvector(graph)[1],
                                                  'tn_authority': vp_authority,
                                                  'tn_hub': vp_hub,
                                                  'tn_lcc':  gt.local_clustering(graph)
                                                  }.items()}

    for attrs in product(graph.vertices(), measures.items()):
        append_val(*get_attrs(attrs))

    return pd.DataFrame(dict(map(lambda item: (item[0], item[1][0]), measures.items()))).fillna(0)


def merge_graph_feats_with_tweet_feats(graph_features):
    features = pd.read_csv(pj(FEATURES_DIR, FEATURES_FILENAME), header=0)
    features = features.join(graph_features.set_index(['tp_group', 'tp_author']),
                             on=['tp_group', 'tp_author']).fillna(0)
    features.to_csv(pj(FEATURES_DIR, FEATURES_INC_GRAPH_FILENAME), index=False)
    return features
