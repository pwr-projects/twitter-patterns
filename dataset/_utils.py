#!/bin/python
import os
import re
import shutil
import string
from collections import Counter, defaultdict
from itertools import chain, product
from typing import Dict, Sequence, Set

import emoji
import nltk
import numpy as np
import pandas as pd
import twint
from langdetect import detect_langs
from tqdm import tqdm

GROUPS = ['musicians',
          'actors',
          'celebrities',
          'athletes',
          'politicians']

TWEETS_DIR = 'tweets'
TWEETS_FILENAME = 'tweets.csv'
USERS_FILENAME = 'users.csv'
TEMP_DIR = '.tmp'
USERS_LIST_DIR = 'users_lists'


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


def download_hashtags(*hashtags: Sequence[str], tweets_limit: int = 10000):
    if os.path.isdir('hashtags'):
        shutil.rmtree('hashtags')
    config = twint.Config()
    config.Search = ' '.join('#' + hashtag for hashtag in hashtags)
    config.Lang = 'en'
    config.Store_csv = True
    config.Output = 'temp/hashtags'
    config.User_full = True
    config.Followers = True
    config.Limit = tweets_limit
    config.Lowercase = True
    config.Verified = True
    twint.run.Search(config)


def scrap_tweets(user: str, group: str, limit: int = 100000):
    if user is None:
        return
    config = twint.Config()
    config.Username = user
    config.Limit = limit
    config.Output = f'tweets/{group}'
    config.Store_csv = True
    config.Lang = 'en'
    config.Custom['group'] = group
    config.Hide_output = False
    config.Format = '{id}'
    twint.run.Search(config)


def download_followers(username: str, usergroup: str, function=twint.run.Followers):
    config = twint.Config()
    config.Username = username
    config.Lang = 'en'
    config.Store_csv = True
    config.Output = f'followers/{usergroup}/{username}.csv'
    # config.Limit = limit
    config.Lowercase = True
    # config.Hide_output = True
    function(config)


def extract_tweet_authors() -> Sequence[str]:
    content = pd.read_csv('temp/hashtags/tweets.csv', header=0)
    return content.username.unique()


def get_users_with_lower_bound(min_followers: int = 10000) -> Sequence[str]:
    assert min_followers > 0, 'min_followers should be greater than 0'
    content = pd.read_csv('temp/followers/users.csv', header=0)[['username', 'followers']].drop_duplicates('username')
    return to_lower(content[content.followers > min_followers].username)


def find_duplicates(groups: Dict[str, Sequence[str]], other_users: Sequence[str] = list()) -> Set[str]:
    return set(k for k, v in Counter(chain(*groups.values(), other_users)).items() if v > 1)


def add_not_duplicates(groups: Dict[str, Set[str]], category: str, users: Sequence[str]):
    to_add = set(users) - find_duplicates(groups, users)
    groups[category].update(to_add)
    return groups


def create_group_dict(*categories: Sequence[str]) -> Dict[str, Set[str]]:
    groups = {}
    for category in tqdm(categories, 'Reading group file'):
        with open(f'{category}.txt', mode='r') as f:
            users = set(map(lambda elem: elem.strip(), f.readlines()))
        groups[category] = users
    return groups


def create_group_dict_from_tweets(*categories: Sequence[str]) -> Dict[str, Set[str]]:
    groups = {}
    for category in tqdm(categories, 'Reading tweet file'):
        groups[category] = pd.read_csv(f'tweets/{category}/tweets.csv').username.unique().tolist()
    return groups


def export_dict_to_files(groups: Dict[str, Set[str]]):
    for group_name, users in groups.items():
        outpath = f'{group_name}.txt'
        print(f'Exporting {group_name} to {outpath}')
        with open(outpath, mode='w') as f:
            f.write('\n'.join(users))


def merge_with_scraped(group_name: str, other_users: Sequence['str']):
    groups = create_group_dict(group_name)
    groups = add_not_duplicates(groups, group_name, other_users)
    export_dict_to_files(groups)
    return groups


def tweeter_user_lang_detect(
        user: str, limit: int = 10, csv_path: str = 'tweets/tweets.csv', delete_csv: bool = True, scrap: bool = True) ->str:
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
        tweet = re.sub(r'http\S+', '', tweet) if remove_url else tweet
        tweet = str(tweet).translate(str.maketrans({key: None for key in string.punctuation}))
        tweet = nltk.word_tokenize(tweet)
        tweet = map(lambda word: word.lower(), tweet)
        tweet = filter(lambda word: not word.startswith('@'), tweet) if remove_mentions else tweet
        tweet = map(lemmatizer.lemmatize, tqdm(tweet, 'Lemmatizing')) if lemma else tweet
        tweet = ' '.join(tweet)
        if tweet:
            preprocessed_tweets.append(tweet)
    return preprocessed_tweets


class TweetCleaner():
    def __init__(self):
        self._tokenizer = nltk.tokenize.TweetTokenizer()
        self._lemmatizer = nltk.stem.WordNetLemmatizer()
        self._stop_words = set(nltk.corpus.stopwords.words('english'))

    def emotional_clean(self, tweet: str) -> str:
        if tweet:
            tweet = tweet.lower()
            tweet = self._tokenizer.tokenize(tweet)
            tweet = [word for word in tweet if word not in self._stop_words]
            tweet = [self._lemmatizer.lemmatize(word) for word in tweet]
            tweet = [word for word in tweet if re.match(r'^[a-z]+$', word) or word in emoji.UNICODE_EMOJI]

            return tweet
        
        return []