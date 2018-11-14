#!/bin/python
import multiprocessing as mp
from functools import partial

from tqdm import tqdm

from _utils import *
from _nicknames_web_scraper import download_category, filter_and_export

considered_groups = ['politicians',
                     'athletes',
                     'actors',
                     'musicians',
                     'celebrities']

## Downloading twitter nicks from the page with nicks
groups = download_category(*considered_groups)
# Filtering (removing duplicates etc) and exporting to files
filter_and_export(considered_groups, groups)

# Download more celebrities

# enter hashtags to scrap just so (it's *args)
# Download tweets with given hashtags specific to some group, which will allow to extract well-known users.
download_hashtags('fashionmodel', tweets_limit=100000)

# Extracting authors of tweets from downloaded dataset of tweets with prevously mentioned hashtags
for user in tqdm(extract_tweet_authors(), 'Downloading users followers'):
    # Downloading followes of tweets authors
    download_followers(user)

# Extracting users with at least *min_followers* followers.
# Merging with downloaded users from web at the very first step
merge_with_scraped('celebrities', get_users_with_lower_bound(min_followers=5000))


## politicians stuff
groups = merge_with_scraped('politicians', only_lang_users('adds/politicians.csv', 'adds/filtered_politicians.csv'))

summary_dict(groups)
# #######################
# # SCRAPING!!!! :3
# # TODO CHECK OPTIONS


# def scrap_group(group_name, groups=groups):
#     with mp.Pool(1) as p:
#         p.map(partial(scrap_twits, group=group_name, limit=100000), groups[group_name])

# processes = [mp.Process(target=scrap_group, args=(group_name,)) for group_name in considered_groups]
# for process in processes:
#     process.start()
# for process in processes:
#     process.join()

