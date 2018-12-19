import os
import re
import string
from os.path import join as pj
from typing import Dict, Set

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
                     remove_stopwords: bool = True,
                     remove_url: bool = True,
                     remove_mentions: bool = True,
                     remove_punctuation: bool = True,
                     to_lower: bool = True,
                     ):
    tweet = re.sub(r'(?:(?:(?:www|http)[:/]*)*\S+(?:\.(?:com|org|pl))(?:/\S+)*)', '', tweet) if remove_url else tweet
    tweet = tweet.replace('#', '') if remove_hashes else tweet
    tweet = Text(tweet).words
    tweet = filter(lambda word: word not in STOPWORDS, tweet) if remove_stopwords else tweet
    tweet = ' '.join(tweet).translate(str.maketrans({key: None for key in string.punctuation})).split()
    tweet = map(lambda word: word.lower(), tweet) if to_lower else tweet
    tweet = filter(lambda word: not word.startswith('@'), tweet) if remove_mentions else tweet
    tweet = map(LEMMATIZER.lemmatize, tqdm(tweet, 'Lemmatizing')) if lemma else tweet
    return list(filter(None, tweet))


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
            merged_tweets = pd.concat([merged_tweets, tweets])

    merged_tweets.to_csv(pj(TWEETS_DIR, f'{group_name}.csv'))

def merge_tweets_of_all_groups():
    for group_name in tqdm(GROUPS, 'Tweets merging: group'):
        merge_group_tweets(group_name)
