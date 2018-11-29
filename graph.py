# %%
try:
    import graph_tool.all as gt
except ImportError:
    print('Install graph-tool for python>3.5, please ;-;')
    exit(-1)


from config import *
from tqdm import tqdm
from typing import Dict, Sequence
import pandas as pd
from dataset.stats import get_mentions

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
    graph.save(graph_path, graph_format)
    return graph

get_mentions(True)
get_mentions(False)
exit(0)
# %%
mentions = get_mentions(False)

#%%

# %%
g = create_graph(mentions)
# %%
layout = gt.sfdp_layout(g, groups=g.vp.group)
gt.graph_draw(g, pos=layout, vertex_fill_color=g.vp.group)


#%%
