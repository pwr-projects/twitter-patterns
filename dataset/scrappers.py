import os
import shutil
from os.path import join as pj
from typing import Sequence

import twint
from tqdm import tqdm

from config import FOLLOWERS_DIR, HASHTAG_DIR, TWEETS_DIR

from .loaders import (extract_athors_from_tweets,
                      get_users_with_min_followers_no)
from .utils import merge_with_scraped


def download_hashtags(*hashtags: Sequence[str], tweets_limit: int = 10000):
    if os.path.isdir(HASHTAG_DIR):
        shutil.rmtree(HASHTAG_DIR)
    config = twint.Config()
    config.Search = ' '.join('#' + hashtag for hashtag in hashtags)
    config.Lang = 'en'
    config.Store_csv = True
    config.Output = HASHTAG_DIR
    config.User_full = True
    config.Followers = True
    config.Limit = tweets_limit
    config.Lowercase = True
    config.Verified = True
    twint.run.Search(config)


def scrap_tweets(user: str, group: str, limit: int = 100000):
    path = pj(TWEETS_DIR, group, user)

    if user is None or os.path.isdir(path):
        print(f'{user}\'s tweets already downloaded')
        return

    print(f'Started downloading {user}\'s tweets...')

    config = twint.Config()
    config.Username = user
    config.Limit = limit
    config.Output = path
    config.Store_csv = True
    config.Lang = 'en'
    config.Hide_output = False
    # config.Format = '{id}'
    twint.run.Search(config)


def download_followers(username: str, usergroup: str = '', function=twint.run.Followers):
    config = twint.Config()
    config.Username = username
    config.Lang = 'en'
    config.Store_csv = True
    config.Output = pj(FOLLOWERS_DIR, usergroup, username)
    config.Lowercase = True
    function(config)


def get_extra_users_from_hashtags(group_name: str, low_followers_bound: int, *hashtags: Sequence[str]):
    download_hashtags(hashtags, tweets_limit=100000)

    for user in tqdm(extract_athors_from_tweets(HASHTAG_DIR), 'Downloading users followers'):
        download_followers(user)

    merge_with_scraped(group_name, get_users_with_min_followers_no(FOLLOWERS_DIR, min_followers=low_followers_bound))
