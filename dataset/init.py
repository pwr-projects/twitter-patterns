#!/bin/python
import multiprocessing as mp
import sys
from functools import partial

import twint
from tqdm import tqdm

from _nicknames_web_scraper import download_category, filter_and_export
from _utils import *

considered_groups = ['politicians',
                     'athletes',
                     'actors',
                     'musicians',
                     'celebrities']

# Downloading twitter nicks from the page with nicks
# groups = download_category(*considered_groups)
# # Filtering (removing duplicates etc) and exporting to files
# filter_and_export(considered_groups, groups)

# # Download more celebrities

# # enter hashtags to scrap just so (it's *args)
# # Download tweets with given hashtags specific to some group, which will allow to extract well-known users.
# download_hashtags('fashionmodel', tweets_limit=100000)

# # Extracting authors of tweets from downloaded dataset of tweets with prevously mentioned hashtags
# for user in tqdm(extract_tweet_authors(), 'Downloading users followers'):
#     # Downloading followes of tweets authors
#     download_followers(user)

# # Extracting users with at least *min_followers* followers.
# # Merging with downloaded users from web at the very first step
# merge_with_scraped('celebrities', get_users_with_lower_bound(min_followers=5000))


# ## politicians stuff
# merge_with_scraped('politicians', only_lang_users('adds/politicians.csv', 'adds/filtered_politicians.csv'))

# summary_dict(groups, 'Final')
# #######################
# # SCRAPING!!!! :3
# # TODO CHECK OPTIONS

# groups = create_group_dict(*considered_groups)


# żeby się scrapowali tylko ci, których tweety mamy, upewnij się, że masz pliki dataset/tweets/{nazwa grupy}/tweets.csv
groups = create_group_dict_from_tweets(sys.argv[1]) 

def get_batch(group_name, batch_size: int, batch_idx: int):
    data = list(groups[group_name])
    first = batch_size * batch_idx
    last = batch_size * (batch_idx + 1)
    last = last if last < len(data) else len(data)
    return data[first:last]


processes = [mp.Process(target=download_followers, args=(username, sys.argv[1], twint.run.Followers))
             for username in get_batch(sys.argv[1], 5, int(sys.argv[2]))]

[p.start() for p in processes]
[p.join() for p in processes]

# !!!!!!!!!!!!!!!!!!!
# skrypt uruchamia się przez ./init.py {nazwa grupy} {batch id}
# zrobiłem tak, bo nie chciało mi się synchronizować wątków, a uruchomionych 5 jest max dla twinta, żeby nie wywalił
# nie jest to efektywne, bo za kazdym uruchomieniem skryptu tworzy się `groups` na podstawie tweetów podanej grupy, więc dość długo :c
# jakbym mógł przetestować, to bym zmienił
# jak komuś się chce to można przepisać