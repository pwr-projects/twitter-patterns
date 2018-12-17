# %%
import os
import pickle as pkl
from itertools import chain
from typing import Dict, Sequence

import numpy as np
import pandas as pd
from tqdm import tqdm

from config import (GROUPS, RESOURCE_DIR, TEMP_DIR, TWEETS_DIR,
                    TWEETS_FILENAME, only_classified_users_str)

from dataset import get_mentions_path, get_mentions, wc

try:
    import graph_tool.all as gt
except ImportError:
    print('Install graph-tool for python>3.5, please ;-;')
    exit(-1)


# %%

def create_graph(only_classified_users: bool, override: bool = False):
    only_for_classified = only_classified_users_str(only_classified_users)
    graph_path = os.path.join(TEMP_DIR, f'graph_{only_for_classified}.ml')
    graph_format = 'graphml'

    if not override and os.path.isfile(graph_path):
        return gt.load_graph(graph_path, graph_format)

    graph = gt.Graph(directed=True)

    # vp_group = graph.new_vp('string')
    vp_group = graph.new_vp('int')
    vp_username = graph.new_vp('string')
    ep_weight = graph.new_ep('int')

    graph.vp.group = vp_group
    graph.vp.username = vp_username
    graph.ep.weight = ep_weight

    def get_vertex_and_create_if_not_exist(group: str, username: str):
        v = gt.find_vertex(graph, graph.vp.username, username)

        if not v:
            v = graph.add_vertex()
            graph.vp.group[v] = GROUPS.index(group)
            # graph.vp.group[v] = group
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

    all_mentions_path, exists = get_mentions_path(only_classified_users)

    if not exists:
        get_mentions(only_classified_users)

    for data in tqdm(pd.read_csv(all_mentions_path, header=0, chunksize=500),
                     total=int((wc(all_mentions_path) - 1) / 500),
                     desc='Creating graph',
                     leave=False):
        [add_vartices_and_edges(row.group, row.username, row.mentioned) for row in data.itertuples()]

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
                         display_props=[g.vp.group, g.vp.username]
                         #   output=os.path.join(RESOURCE_DIR, 'graph.pdf'),
                         )


# %%
g = create_graph(True)
g = gt.GraphView(g, vfilt=gt.label_largest_component(g))
g.purge_vertices()
state = gt.minimize_nested_blockmodel_dl(g, deg_corr=True, verbose=True)
t = gt.get_hierarchy_tree(state)[0]
tpos = pos = gt.radial_tree_layout(t, t.vertex(t.num_vertices() - 1), weighted=True)
cts = gt.get_hierarchy_control_points(g, t, tpos)
pos = g.own_property(tpos)
b = state.levels[0].b
shape = b.copy()
shape.a %= 14
gt.graph_draw(g,
              pos=pos,
              edge_pen_width=0.1,
              vertex_fill_color=g.vp.group,
              vertex_shape=shape,
              vertex_size=gt.prop_to_size(g.degree_property_map('total'), ma=20, mi=3),
              edge_control_points=cts,
              edge_color='white',
              bg_color=[0.0, 0.0, 0.0, 1.0],
              vertex_anchor=0,
              display_props=[g.vp.group, g.vp.username],
              output=os.path.join(RESOURCE_DIR, 'graph.pdf'),
              )
