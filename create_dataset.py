#!/bin/python
import multiprocessing as mp
import sys
from functools import partial

import twint
from tqdm import tqdm

from dataset.nicknames_web_scraper import download_dataset
from dataset.utils import *
from config import *

download_dataset(GROUPS)

## GET MORE CELEBRITIES
get_extra_user_from_hashtags('celebrities', 'fashionmodel')


# politicians stuff
merge_with_scraped('politicians', only_lang_users(os.path.join(USERS_LIST_DIR, 'politicians.csv'),
                                                  os.path.join(USERS_LIST_DIR, 'politicians.csv')))



groups = create_group_dict_from_tweets(*GROUPS)
summary_dict(groups, 'Final')

for group in sys.argv[1:]:
    mp.Pool(2).map(partial(scrap_tweets, group=group), groups[group])