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


def get_mentions_from_tweet_with_idx(idx_tweet):
    mentions = get_mentioned_users_from_tweet(idx_tweet[1])
    return [[idx_tweet[0], ] * len(mentions), mentions]


def extract_mentions(group):
    outfile_path = os.path.join(TEMP_DIR, f'{group}_mentions.csv')

    if os.path.isfile(outfile_path):
        print(f'Loading {group} mention from {outfile_path}...')
        return pd.read_csv(outfile_path, header=0)

    mentions_dict = {'group': [], 'username': [], 'mentioned': []}
    tweets = pd.read_csv(os.path.join(TWEETS_DIR, group, TWEETS_FILENAME),
                         header=0,
                         memory_map=True,
                         dtype=str)

    unique_users = tweets.username.unique()
    max_name_length = max(map(len, unique_users))

    for user in tqdm(unique_users, 'Mentions: extract', leave=False):
        mentions = list(chain(*map(get_mentioned_users_from_tweet,
                                   tweets[tweets.username == user].tweet.values)))

        for mentioned_user in mentions:
            mentions_dict['group'].append(group)
            mentions_dict['username'].append(user)
            mentions_dict['mentioned'].append(mentioned_user)

    pd.DataFrame(mentions_dict).drop_duplicates().to_csv(outfile_path, index=False)


def extract_mentions_faster(group):
    mentions_dict = {'group': [], 'username': [], 'mentioned': []}

    outfile_path = os.path.join(TEMP_DIR, f'{group}_mentions.csv')

    if os.path.isfile(outfile_path):
        print(f'Loading {group} mention from {outfile_path}...')
        return pd.read_csv(outfile_path, header=0)

    tweets_path = os.path.join(TWEETS_DIR, group, TWEETS_FILENAME)
    for data in tqdm(pd.read_csv(tweets_path,
                                 header=0,
                                 chunksize=chunksize,
                                 dtype=str),
                     'Mentions: extract',
                     total=int((wc(tweets_path) - 1) / chunksize),
                     leave=False):
        mentions = chain(map(get_mentions_from_tweet_with_idx,
                             enumerate(data.tweet.values)))

        mentions = np.array(list(filter(lambda x: len(x[1]), mentions)), object)

        if not mentions.size:
            continue

        ids = list(chain(*mentions[:, 0]))
        groups = [group, ] * len(ids)

        mentions_dict['group'].extend(groups)
        mentions_dict['username'].extend(np.take(data.username.tolist(), ids))
        mentions_dict['mentioned'].extend(list(chain(*mentions[:, 1])))

    mentions = pd.DataFrame(mentions_dict).drop_duplicates()
    mentions = mentions[mentions.username != mentions.mentioned]
    mentions.to_csv(outfile_path, index=False)
    return mentions


def get_mentions_path(only_classified_users):
    only_for_classified = only_classified_users_str(only_classified_users)
    all_mention_path = os.path.join(TEMP_DIR, f'all_mentions_{only_for_classified}.csv')
    return all_mention_path, os.path.isfile(all_mention_path)


def get_mentions(only_classified_users=False):
    all_mentions_path, _ = get_mentions_path(only_classified_users)
    all_mentions = []

    if os.path.isfile(all_mentions_path):
        print(f'Found all mentions in {all_mentions_path}. Loading...')
        return pd.read_csv(all_mentions_path, header=0)

    gbar = tqdm(GROUPS, 'Mentions: process', leave=False)
    for group in gbar:
        gbar.set_postfix(group=group)
        mentions = extract_mentions_faster(group)
        all_mentions.append(mentions)

    mentions = pd.concat(all_mentions, ignore_index=True)
    unique_usernames = mentions.username.unique()

    if only_classified_users:
        tqdm.pandas(desc='Processing mentions')
        mentions = mentions[mentions.progress_apply(lambda x: x.mentioned in unique_usernames,
                                                    axis='columns')]

    print(f'Saving all mentions to {all_mentions_path}...')
    mentions.to_csv(all_mentions_path, index=False)
    return mentions
