#!/bin/python
# %%
import multiprocessing as mp
import os
import sys
from functools import partial

import twint
from tqdm import tqdm

from config import USERLISTS_HELPERS_DIR
from dataset import (create_group_dict_from_userlists, download_dataset,
                     get_extra_users_from_hashtags,
                     get_tweets_with_filtered_users, merge_with_scraped,
                     only_lang_users, scrap_tweets, summary_dict)

# %%
# download_dataset()


# GET MORE CELEBRITIES
# get_extra_users_from_hashtags('celebrities', 'fashionmodel')


# politicians stuff
# merge_with_scraped('politicians', only_lang_users(os.path.join(USERLISTS_HELPERS_DIR, 'politicians.txt'),
#                                                   os.path.join(USERLISTS_HELPERS_DIR, 'politicians.txt')))

# %%
groups = create_group_dict_from_userlists()
groups['politicians'] = get_tweets_with_filtered_users('politicians', 7500)[1]
# groups['musicians'] = get_tweets_with_filtered_users('musicians')[1]
summary_dict(groups, 'final')


for group in sys.argv[1:]:
    mp.Pool(2).map(partial(scrap_tweets, group=group), groups[group])

# %%
