import os
import shutil
from typing import Sequence

import twint

from config import *


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
    path = os.path.join(TWEETS_DIR, group, user)

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
    config.Output = os.path.join(FOLLOWERS_DIR, usergroup, username)
    config.Lowercase = True
    function(config)
