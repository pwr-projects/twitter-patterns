#!/bin/python
import multiprocessing as mp
import sys
from functools import partial

import twint
from tqdm import tqdm

from _nicknames_web_scraper import download_category, filter_and_export
from _utils import *

# #######################
# # SCRAPING!!!! :3
# # TODO CHECK OPTIONS

# groups = create_group_dict(*considered_groups)
# żeby się scrapowali tylko ci, których tweety mamy, upewnij się, że masz pliki dataset/tweets/{nazwa grupy}/tweets.csv
groups = create_group_dict_from_tweets(*GROUPS)
p = mp.Pool(2)
p.map(partial(download_followers, usergroup=sys.argv[1], function=twint.run.Followers), groups[sys.argv[1]])

# !!!!!!!!!!!!!!!!!!!
# skrypt uruchamia się przez ./init.py {nazwa grupy} {batch id}
# zrobiłem tak, bo nie chciało mi się synchronizować wątków, a uruchomionych 5 jest max dla twinta, żeby nie wywalił
# nie jest to efektywne, bo za kazdym uruchomieniem skryptu tworzy się `groups` na podstawie tweetów podanej grupy, więc dość długo :c
# jakbym mógł przetestować, to bym zmienił
# jak komuś się chce to można przepisać
