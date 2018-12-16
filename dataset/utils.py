import os
import re
import shutil
import string
from collections import Counter, defaultdict
from itertools import chain, product
from subprocess import check_output
from typing import Dict, Sequence, Set

import nltk
import numpy as np
import pandas as pd
import twint
from langdetect import detect_langs
from tqdm import tqdm

from config import *

from .scrappers import *

nltk.download('punkt')


def wc(filename):
    return int(check_output(['wc', '-l', filename]).split()[0])


def load_userlist_from_file(filename: str, filepath: str = USERLISTS_HELPERS_DIR):
    with open(os.path.join(filepath, filename), 'r') as f:
        users = f.readlines()
    users = map(lambda user: user.replace('\n', ''), users)
    return set(users)

def get_group_tweets(groupname:str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(TWEETS_DIR, groupname, TWEETS_FILENAME), header=0)

def get_batch(groups, group_name, batch_size: int, batch_idx: int):
    data = list(groups[group_name])
    first = batch_size * batch_idx
    last = batch_size * (batch_idx + 1)
    last = last if last < len(data) else len(data)
    return data[first:last]


def summary_html(summary: Dict[str, str], title: str) -> str:
    print(title)
    html = f'<table><tr><th>Category</th><th>Count</th></tr>'
    for k, v in summary.items():
        html += f'<tr><td>{k}</td><td>{len(v)}</td></tr>' if v else ''
    html += '</table>'
    return html


def summary_dict(summary: Dict[str, Sequence[str]], title: str):
    print(title)
    format = '{:15s}\t{:5d}'
    print('{:15s}\t{:5s}'.format('Category', 'Count'))
    for k, v in summary.items():
        if len(v):
            print(format.format(k, len(v)))


def to_lower(strs: Sequence['str']):
    return list(map(lambda elem: elem.lower(), strs))


def extract_tweet_authors(tweets_dir: str) -> Sequence[str]:
    content = pd.read_csv(os.path.join(tweets_dir, TWEETS_FILENAME), header=0)
    return content.username.unique()


def get_users_with_min_followers_no(users_dir: str, min_followers: int) -> Sequence[str]:
    assert min_followers > 0, 'min_followers should be greater than 0'
    content = pd.read_csv(os.path.join(users_dir, USERS_FILENAME), header=0)
    content = content[['username', 'followers']].drop_duplicates('username')
    return to_lower(content[content.followers > min_followers].username)


def get_duplicates_in_dict(groups: Dict[str, Sequence[str]], other_users: Sequence[str] = list()) -> Set[str]:
    return set(k for k, v in Counter(chain(*groups.values(), other_users)).items() if v > 1)


def add_not_duplicates(groups: Dict[str, Set[str]], category: str, users: Sequence[str]):
    to_add = set(users) - get_duplicates_in_dict(groups, users)
    groups[category].update(to_add)
    return groups


def create_group_dict_from_userlists(*categories: Sequence[str], userlist_dir: str = USERS_LIST_DIR) -> Dict[str, Set[str]]:
    groups = {}
    for category in tqdm(categories, 'Reading group file'):
        with open(os.path.join(USERS_LIST_DIR, f'{category}.txt'), mode='r') as f:
            users = set(map(lambda elem: elem.strip(), f.readlines()))
        groups[category] = users
    return groups


def create_group_dict_from_tweets(*categories: Sequence[str], tweets_dir: str = TWEETS_DIR) -> Dict[str, Set[str]]:
    groups = {}
    for category in tqdm(categories, 'Reading tweet file'):
        groups[category] = pd.read_csv(os.path.join(tweets_dir, category, TWEETS_FILENAME)).username.unique().tolist()
    return groups


def export_users_dict_to_files(groups: Dict[str, Set[str]], outdir: str = TEMP_DIR):
    for group_name, users in groups.items():
        outpath = f'{group_name}.txt'
        print(f'Exporting {group_name} to {outpath}')
        with open(outpath, mode='w') as f:
            f.write('\n'.join(users))


def merge_with_scraped(group_name: str, other_users: Sequence['str']):
    groups = create_group_dict_from_userlists(group_name, userlist_dir=RAW_USERLISTS_FROM_PAGE)
    groups = add_not_duplicates(groups, group_name, other_users)
    export_users_dict_to_files(groups)
    return groups


def tweeter_user_lang_detect(user: str,
                             limit: int = 10,
                             csv_path: str = os.path.join(TWEETS_DIR, TWEETS_FILENAME),
                             delete_csv: bool = True,
                             scrap: bool = True) -> str:
    try:
        if scrap:
            scrap_tweets(user=user, limit=limit, group='')
        tweets = pd.read_csv(csv_path, header=0)
    except:
        with open('failed.txt', 'a') as myfile:
            print('failed')
            myfile.write(user + '\n')
        return (0, 'bug')

    lang_probs = defaultdict(list)

    for tweetLang in chain(*[detect_langs(i) for i in preprocess_tweets(list(tweets.tweet), lemma=False)]):
        lang_probs[tweetLang.lang].append(tweetLang.prob)

    if delete_csv:
        os.remove(csv_path)
        os.remove(csv_path.replace('tweets.csv', 'users.csv'))

    return max((np.mean(v), k) for k, v in lang_probs.items())[1]


def only_lang_users(nicks_csv_path: str, output_path: str = None, lang: str = 'en') -> Sequence[str]:
    with open(nicks_csv_path, mode='r') as f:
        nicks = [nick.strip() for nick in f.readlines()]

    lang_users = [nick for nick in tqdm(nicks, 'Checking users language')
                  if tweeter_user_lang_detect(nick) == lang]

    if output_path:
        np.savetxt(output_path, lang_users, delimiter='\n', fmt='%s')
    return lang_users


def preprocess_tweets(tweets: Sequence[str], lemma: bool = True, remove_url: bool = True, remove_mentions: bool = True) -> Sequence[str]:
    lemmatizer = nltk.stem.WordNetLemmatizer()
    preprocessed_tweets = []
    for tweet in tqdm(tweets, desc='preprocessing tweets'):
        tweet = tweet.replace('#', '')
        tweet = re.sub(r'(?:(?:(?:www|http)[:/]*)*\S+(?:\.(?:com|org|pl))(?:/\S+)*)',
                       '', tweet) if remove_url else tweet
        tweet = str(tweet).translate(str.maketrans({key: None for key in string.punctuation}))
        tweet = nltk.word_tokenize(tweet)
        tweet = map(lambda word: word.lower(), tweet)
        tweet = filter(lambda word: not word.startswith('@'), tweet) if remove_mentions else tweet
        tweet = map(lemmatizer.lemmatize, tqdm(tweet, 'Lemmatizing')) if lemma else tweet
        tweet = ' '.join(tweet)
        if tweet:
            preprocessed_tweets.append(tweet)
    return preprocessed_tweets


def get_extra_users_from_hashtags(group_name: str, low_followers_bound: int, *hashtags: Sequence[str]):
    download_hashtags(hashtags, tweets_limit=100000)

    for user in tqdm(extract_tweet_authors(HASHTAG_DIR), 'Downloading users followers'):
        download_followers(user)

    merge_with_scraped(group_name, get_users_with_min_followers_no(FOLLOWERS_DIR, min_followers=low_followers_bound))


def get_tweets_with_filtered_users(group: str, tweet_count_threshold: int):
    print('Reading tweet file...')
    tweets = pd.read_csv(os.path.join(TWEETS_DIR, group, TWEETS_FILENAME),
                         low_memory=False,
                         header=0)

    print('Filtering users...')
    filtered_users = tweets.groupby('username')['id'].count().reset_index(name='count')
    filtered_users = filtered_users.sort_values('count')
    filtered_users = filtered_users[filtered_users['count'] > tweet_count_threshold]

    print('Filtering tweets...')
    tweets = tweets[tweets.username.isin(filtered_users.username)]

    return tweets, filtered_users
