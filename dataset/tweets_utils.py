import os
import pickle
import re
import string
from os.path import join as pj
from typing import Dict, Set

import emoji
import nltk
import pandas as pd
from nltk.corpus import stopwords
from polyglot.text import Text
from tqdm import tqdm

from config import GROUPS, TWEETS_DIR, TWEETS_FILENAME

from .loaders import get_user_tweets_of_group

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

STOPWORDS = set(stopwords.words('english'))
LEMMATIZER = nltk.stem.WordNetLemmatizer()


def preprocess_tweet(tweet: str,
                     lemma: bool = True,
                     remove_hashes: bool = True,
                     remove_stopwords: bool = False,
                     remove_url: bool = True,
                     remove_mentions: bool = True,
                     remove_punctuation: bool = True,
                     to_lower: bool = False,
                     ):
    tweet = re.sub(
        r'(?:(?:(?:www|http|https)[:/]*)*\S+(?:\.(?:\w{2,}))(?:/\S+)*)', '<url>', tweet) if remove_url else tweet
    tweet = re.sub(r'#[\w\d_-]+', '<hashtag>', tweet) if remove_hashes else tweet
    tweet = re.sub(r'@\w+', '<user>', tweet) if remove_mentions else tweet
    # tweet = Text(tweet).words
    # tweet = filter(lambda word: word not in STOPWORDS, tweet) if remove_stopwords else tweet
    # tweet = map(lambda word: word.lower(), tweet) if to_lower else tweet
    tweet = ' '.join(list(map(LEMMATIZER.lemmatize, tweet.split()))) if lemma else tweet
    tweet = tweet.translate(str.maketrans({key: None for key in ',.:"?!/\\;\'][{}+_-=)(*&^%$#@~'}))
    return tweet


def create_group_dict_from_tweets(tweets_dir: str = TWEETS_DIR) -> Dict[str, Set[str]]:
    groups_users = {}

    for group_name in tqdm(GROUPS, 'Reading tweet file'):
        file_path = pj(tweets_dir, group_name, TWEETS_FILENAME)
        groups_users[group_name] = set(pd.read_csv(file_path).username)

    return groups_users


def merge_group_tweets(group_name):
    merged_tweets = None
    group_path = os.path.join(TWEETS_DIR, group_name)

    user_names = [dirname for dirname in os.listdir(group_path) if os.path.isdir(pj(group_path, dirname))]

    for username in tqdm(user_names, 'Tweets merging: user', leave=False):
        tweets = get_user_tweets_of_group(username, group_name, low_memory=False)
        tweets['group'] = group_name
        tweets['scraped_user'] = username

        if merged_tweets is None:
            merged_tweets = tweets
        else:
            merged_tweets = pd.concat([merged_tweets, tweets], ignore_index=True)

    merged_tweets.to_csv(pj(TWEETS_DIR, f'{group_name}.csv'))


def merge_tweets_of_all_groups():
    for group_name in tqdm(GROUPS, 'Tweets merging: group'):
        merge_group_tweets(group_name)


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


def get_n_longest_tweets_in_group(group_name, n):
    cleaner = TweetCleaner()
    merged_tweets = None
    group_path = os.path.join(TWEETS_DIR, group_name)

    user_names = [dirname for dirname in os.listdir(group_path) if os.path.isdir(pj(group_path, dirname))]
    group_tweets = None
    for username in user_names:
        tweets = get_user_tweets_of_group(username, group_name, low_memory=False)

        tweets['group'] = group_name
        tweets['scraped_user'] = username
        tweets.reset_index()
        tweets = tweets[tweets.username == tweets.scraped_user]

        tweets.index = tweets.tweet.str.len()
        tweets = tweets.sort_index(ascending=False).reset_index(drop=True)
        tweets = tweets.groupby('username').head(n).reset_index(drop=True)
        tweets.tweet = tweets.tweet.apply(lambda x: ' '.join(cleaner.emotional_clean(x)))
        tweets.tweet = tweets.tweet.apply(preprocess_tweet)

        if group_tweets is None:
            group_tweets = tweets
        else:
            group_tweets = group_tweets.append(tweets)
    return group_tweets


def get_n_longest_tweets(n):
    tweets = None
    for group_name in GROUPS:
        group_tweets = merge_group_tweets(group_name, n)
        if tweets is None:
            tweets = group_tweets
        else:
            tweets.append(group_tweets)

    with open(f'longest_{n}_tweets.pkl', 'wb') as f:
        pickle.dump(tweets, f)

    return tweets
