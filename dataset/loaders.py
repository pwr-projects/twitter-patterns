import os
from os.path import join as pj
from typing import Sequence, Set

import pandas as pd

from config import (TWEETS_DIR, TWEETS_FILENAME, USERLISTS_HELPERS_DIR,
                    USERS_FILENAME)

from .utils import lower_list_of_strs


def extract_athors_from_tweets(tweets_dir: str) -> Set[str]:
    content = pd.read_csv(pj(tweets_dir, TWEETS_FILENAME), header=0)
    return set(content.username)


def load_userlist_from_file(filename: str, filepath: str = USERLISTS_HELPERS_DIR) -> Set[str]:
    with open(pj(filepath, filename), 'r') as f:
        users = f.readlines()
    return set(map(lambda user: user.replace('\n', ''), users))


def get_group_tweets(group_name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(pj(TWEETS_DIR, group_name, TWEETS_FILENAME), header=0, **kwargs)


def get_user_tweets_of_group(username: str, group_name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(pj(TWEETS_DIR, group_name, username, TWEETS_FILENAME), header=0, **kwargs)


def get_users_with_min_followers_no(users_dir: str, min_followers: int) -> Sequence[str]:
    assert min_followers > 0, 'min_followers should be greater than 0'
    content = pd.read_csv(pj(users_dir, USERS_FILENAME), header=0)
    content = content[['username', 'followers']].drop_duplicates('username')
    return lower_list_of_strs(content[content.followers > min_followers].username)


def get_tweets_with_filtered_users(group_name: str, tweet_count_threshold: int):
    print('Reading tweet file...')
    tweets = get_group_tweets(group_name)

    print('Filtering users...')
    filtered_users = tweets.groupby('username')['id'].count().reset_index(name='count')
    filtered_users = filtered_users.sort_values('count')
    filtered_users = filtered_users[filtered_users['count'] > tweet_count_threshold]

    print('Filtering tweets...')
    tweets = tweets[tweets.username.isin(filtered_users.username)]

    return tweets, set(filtered_users.username)
