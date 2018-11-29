import os
import pickle as pkl
import re
import sys
from itertools import chain

import numpy as np
import pandas as pd
from tqdm import tqdm

from config import *

from .utils import *

__all__ = ['get_top_followers',
           'get_mentioned_users_from_tweet',
           'get_mentions',
           'print_stats']


def get_top_followers(threshold: int = 10000, top: bool = False, top_n=None):
    all_users = []

    for group in GROUPS:
        tweets = pd.read_csv(os.path.join(TWEETS_DIR, group, USERS_FILENAME), header=0)
        tweets['group'] = group
        all_users.append(tweets)

    tweets: pd.DataFrame = pd.concat(all_users)
    tweets = tweets[tweets.duplicated('username') == False]
    tweets = tweets[(tweets.followers > 0) & (tweets.followers <= threshold)]
    tweets = tweets[['group', 'username', 'followers']]

    tweets = tweets.sort_values('followers', ascending=not top).groupby('group', sort=False)
    tweets = tweets.head(top_n) if top_n else tweets
    tweets = tweets.groupby(['group', 'username']).sum().reset_index()
    return tweets


def get_mentioned_users_from_tweet(tweet: str):
    return list(map(lambda mention: mention.replace('@', ''), re.findall(r'@[\w\d]+', tweet)))


def extract_mentions(group):
    mentions_dict = {'group': [], 'username': [], 'mentioned': []}

    outfile_path = os.path.join(TEMP_DIR, f'{group}_mentions.pkl')
    override = True

    if os.path.isfile(outfile_path):
        answer = input('Be careful ;_; File exists. Override? ')
        override = answer not in 'Nn'

    if not override:
        with open(outfile_path, 'rb') as f:
            print(f'Loading {group} mention from {outfile_path}...')
            return pkl.load(f)

    tweets = pd.read_csv(os.path.join(TWEETS_DIR, group, TWEETS_FILENAME),
                         header=0,
                         memory_map=True,
                         dtype=str)

    unique_users = tweets.username.unique()
    max_name_length = max(map(len, unique_users))

    for user in tqdm(unique_users, 'Mentions: extract', leave=False):
        mentions = list(chain(*map(get_mentioned_users_from_tweet,
                                   tqdm(tweets[tweets.username == user].tweet.values,
                                        'Tweet', leave=False))))

        for mentioned_user in mentions:
            mentions_dict['group'].append(group)
            mentions_dict['username'].append(user)
            mentions_dict['mentioned'].append(mentioned_user)

    with open(outfile_path, 'wb') as f:
        pkl.dump(pd.DataFrame(mentions_dict).drop_duplicates(), f)


def get_mentions(only_classified_users=False):
    all_mentions = []

    only_classified_group_str = 'inside' if only_classified_users else 'outside'
    all_mentions_path = os.path.join(TEMP_DIR, f'all_mentions_{only_classified_group_str}.pkl')

    if os.path.isfile(all_mentions_path):
        print(f'Found all mentions in {all_mentions_path}. Loading...')
        with open(all_mentions_path, 'rb') as f:
            return pkl.load(f)

    gbar = tqdm(GROUPS, 'Mentions: process', leave=False)
    for group in gbar:
        gbar.set_postfix(group=group)

        mention_path = os.path.join(TEMP_DIR, f'{group}_mentions.pkl')

        if not os.path.isfile(mention_path):
            extract_mentions(group)

        with open(mention_path, 'rb') as f:
            mentions = pkl.load(f, fix_imports=True)

        mentions = mentions.drop_duplicates()
        mentions = mentions[mentions.username != mentions.mentioned]

        all_mentions.append(mentions)


    mentions = pd.concat(all_mentions, ignore_index=True)
    unique_usernames = mentions.username.unique()
    if only_classified_users:
        tqdm.pandas(desc='Processing mentions')
        mentions = mentions[mentions.progress_apply(lambda x: x.mentioned in unique_usernames,
                                           axis='columns')]

    with open(all_mentions_path, 'wb') as f:
        print(f'Saving all mentions to {all_mentions_path}...')
        pkl.dump(mentions, f)

    return mentions


def get_stats(data):
    data = data.groupby(['group', 'username']).count().reset_index()
    return data.groupby('group').agg({'username': 'count', 'mentioned': 'sum'})


def print_stats(groups=GROUPS):
    inside = get_mentions(True)
    not_inside = get_mentions(False)
    print('Only inside')
    print(get_stats(inside))
    print('Ogólne mentiony')
    print(get_stats(not_inside))
