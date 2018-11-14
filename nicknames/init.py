from _download_nicknames import download_category, filter_and_export
from _download_celebrities import *
from tqdm import tqdm

considered_groups = ['politicians',
                     'athletes',
                     'actors',
                     'musicians',
                     'celebrities']

# Downloading twitter nicks from the page with nicks
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
users = get_users_with_lower_bound(min_followers=5000)
# Merging with downloaded users from web at the very first step
merge_with_scraped('celebrities', users)

# SCRAPING!!!! :3
# TODO CHECK OPTIONS
for user in tqdm(users, desc='Scraping user', leave=False):
    scrap_twits(user, limit=100000)
