#!/bin/python3.6
# %%
import os
import pickle as pkl
import re
import sys
from itertools import chain

import numpy as np
import pandas as pd
from tqdm import tqdm

from _utils import GROUPS
tqdm.pandas()

__all__ = ['get_top_followers',
           'get_mentioned_users_from_tweet',
           'get_mentions']


# %%
TWEETS_DIR = 'tweets'
TWEETS_FILENAME = 'tweets.csv'
USERS_FILENAME = 'users.csv'
TEMP_DIR = '.tmp'

if not os.path.isdir(TEMP_DIR):
    os.mkdir(TEMP_DIR)
# %%


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


def get_mentions(groups):
    mentions_dict = {'group': [], 'username': [], 'mentioned': []}

    gbar = tqdm(groups, 'Group')
    for group in gbar:
        gbar.set_postfix(group=group)
        outfile_path = os.path.join(TEMP_DIR, f'{group}_mentions.pkl')
        override = True
        if os.path.isfile(outfile_path):
            answer = input('Be careful ;_; File exists. Override? ')
            override = answer not in 'Nn'
        if not override:
            continue

        tweets = pd.read_csv(os.path.join(TWEETS_DIR, group, TWEETS_FILENAME), header=0, low_memory=False)
        ubar = tqdm(tweets.username.unique(), 'User')
        for user in ubar:
            ubar.set_postfix(user=user)
            mentions = list(chain(*map(get_mentioned_users_from_tweet,
                                       tqdm(tweets[tweets.username == user].tweet.values, 'Tweet'))))
            for mentioned_user in mentions:
                mentions_dict['group'].append(group)
                mentions_dict['username'].append(user)
                mentions_dict['mentioned'].append(mentioned_user)

        with open(outfile_path, 'wb') as f:
            pkl.dump(pd.DataFrame(mentions_dict).drop_duplicates(), f)


# %%
# get_top_followers(10000, 5, True)
# groups = GROUPS if sys.argv[1] in ['all', 'ALL', '-a', '--all'] else sys.argv[1:]
# get_mentions(groups)

# %%
def doTheThing(*groups, only_inside_group=False, verbose=True):
    all_mentions = []
    gbar = tqdm(groups, desc='Group', disable=not verbose)
    for group in gbar:
        gbar.set_postfix(group=group)
        with open(f'.tmp/{group}_mentions.pkl', 'rb') as f:
            mentions = pkl.load(f, fix_imports=True)
        mentions = mentions.drop_duplicates()
        mentions = mentions[mentions.username != mentions.mentioned]
        if only_inside_group:
            mentions = mentions[mentions.apply(lambda x: x.mentioned in x.username,
                                                        axis='columns')]
        all_mentions.append(mentions)

    mentions = pd.concat(all_mentions, ignore_index=True)
    outfile_path = os.path.join(TEMP_DIR, 'all_mentions.pkl')
    with open(outfile_path, 'wb') as f:
        print(f'Saving pickle to {outfile_path}')
        pkl.dump(mentions, f)
    return mentions

groups = GROUPS

inside = doTheThing(*groups, only_inside_group=True, verbose=False)
not_inside = doTheThing(*groups, only_inside_group=False, verbose=False)

# %%
print('Wewnątrz')
inside.groupby(['group', 'username']).count().reset_index().groupby('group').agg({'username': 'count', 'mentioned': 'sum'})
#%%
print('Ogólne mentiony')
not_inside.groupby(['group', 'username']).count().reset_index().groupby('group').agg({'username': 'count', 'mentioned': 'sum'})

#%%
