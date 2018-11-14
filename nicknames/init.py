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

# # Downloading twitter nicks from the page with nicks
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
# users = get_users_with_lower_bound(min_followers=5000)
# # Merging with downloaded users from web at the very first step
# merge_with_scraped('celebrities', users)

groups = create_group_dict(considered_groups)
summary_dict(groups, 'Final')
#######################
# SCRAPING!!!! :3
# TODO CHECK OPTIONS


def scrap_group(group_name, groups=groups):

    # for idx, user in enumerate(groups[group_name], start=1):
    #     print(f'{group_name} {idx}/{len(groups[group_name])}: {user}')
    with mp.Pool(5) as p:
        p.map(partial(scrap_twits, limit=100000), groups[group_name])
    # scrap_twits(user, limit=100000)

processes = [mp.Process(target=scrap_group, args=(group_name,)) for group_name in considered_groups]
for process in processes:
    process.start()
for process in processes:
    process.join()
