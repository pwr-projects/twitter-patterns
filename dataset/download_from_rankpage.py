#!/bin/python
import os

from .nicknames_web_scraper import *
from .utils import *

# Downloading twitter nicks from the page with nicks
groups = download_category(*GROUPS)
# Filtering (removing duplicates etc) and exporting to files
filter_and_export(GROUPS, groups)

download_hashtags('fashionmodel', tweets_limit=100000)
for user in tqdm(extract_tweet_authors(), 'Downloading users followers'):
    # Downloading followes of tweets authors
    download_followers(user)

# Extracting users with at least *min_followers* followers.
# Merging with downloaded users from web at the very first step
merge_with_scraped('celebrities', get_users_with_lower_bound(min_followers=5000))


# politicians stuff
merge_with_scraped('politicians', only_lang_users(os.path.join(USERS_LIST_DIR, 'politicians.csv'),
                                                  os.path.join(USERS_LIST_DIR, 'politicians.csv')))

summary_dict(groups, 'Final')
