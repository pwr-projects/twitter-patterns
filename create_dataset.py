#!/bin/python
#%%
import multiprocessing as mp
import sys
from functools import partial

import twint
from tqdm import tqdm

from config import *

from dataset.nicknames_web_scraper import download_dataset, filter_and_export
from dataset.utils import *
from dataset.mentions import get_mentions

# %%
# download_dataset(GROUPS)


# ## GET MORE CELEBRITIES
# get_extra_users_from_hashtags('celebrities', 'fashionmodel')


# # politicians stuff
# merge_with_scraped('politicians', only_lang_users(os.path.join(USERLISTS_HELPERS_DIR, 'politicians.txt'),
                                                #   os.path.join(USERLISTS_HELPERS_DIR, 'politicians.txt')))

#%%
groups = create_group_dict_from_userlists(*GROUPS)
groups['politicians'] = get_tweets_with_filtered_users('politicians', 7500)[1]
# groups['musicians'] = get_tweets_with_filtered_users('musicians')[1]
summary_dict(groups, 'final')


for group in sys.argv[1:]:
    mp.Pool(2).map(partial(scrap_tweets, group=group), groups[group])

#%%
