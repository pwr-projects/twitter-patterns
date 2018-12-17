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
from nltk.corpus import stopwords
from polyglot.text import Text
from tqdm import tqdm

from config import (FOLLOWERS_DIR, GROUPS, HASHTAG_DIR,
                    RAW_USERLISTS_FROM_PAGE, TEMP_DIR, TWEETS_DIR,
                    TWEETS_FILENAME, USERLISTS_HELPERS_DIR, USERS_FILENAME,
                    USERS_LIST_DIR)

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

STOPWORDS = set(stopwords.words('english'))
LEMMATIZER = nltk.stem.WordNetLemmatizer()


def wc(filename):
    return int(check_output(['wc', '-l', filename]).split()[0])


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


def summary_dict(groups_users: Dict[str, Sequence[str]], title: str):
    print(title)
    format = '{:15s}\t{:5d}'
    print('{:15s}\t{:5s}'.format('Group name', 'Count'))

    for k, v in groups_users.items():
        if len(v):
            print(format.format(k, len(v)))


def lower_list_of_strs(strs: Sequence['str']):
    return list(map(lambda elem: elem.lower(), strs))


def get_duplicates_in_dict(groups_users: Dict[str, Sequence[str]], other_users: Sequence[str] = []) -> Set[str]:
    return set(k for k, v in Counter(chain(*groups_users.values(), other_users)).items() if v > 1)


def add_not_duplicates(groups: Dict[str, Set[str]], category: str, users: Sequence[str]):
    to_add = set(users) - get_duplicates_in_dict(groups, users)
    groups[category].update(to_add)
    return groups


def create_group_dict_from_userlists(userlist_dir: str = USERS_LIST_DIR) -> Dict[str, Set[str]]:
    groups = {}

    for group_name in tqdm(GROUPS, 'Reading group file'):
        with open(os.path.join(USERS_LIST_DIR, f'{group_name}.txt'), mode='r') as f:
            users = set(map(lambda elem: elem.strip(), f.readlines()))

        groups[group_name] = users

    return groups


def create_group_dict_from_tweets(tweets_dir: str = TWEETS_DIR) -> Dict[str, Set[str]]:
    groups_users = {}

    for group_name in tqdm(GROUPS, 'Reading tweet file'):
        file_path = os.path.join(tweets_dir, group_name, TWEETS_FILENAME)
        groups_users[group_name] = set(pd.read_csv(file_path).username)

    return groups_users


def export_users_dict_to_files(groups_users: Dict[str, Set[str]],
                               outdir: str = TEMP_DIR):
    for group_name, users in groups_users.items():
        outpath = f'{group_name}.txt'

        with open(outpath, mode='w') as f:
            f.write('\n'.join(users))


def merge_with_scraped(group_name: str, other_users: Sequence['str']):
    groups_users = create_group_dict_from_userlists(RAW_USERLISTS_FROM_PAGE)
    groups_users = add_not_duplicates(groups_users, group_name, other_users)
    export_users_dict_to_files(groups_users)
    return groups_users


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

    for tweetLang in chain(*[detect_langs(i) for i in preprocess_tweet(tweets.tweet)]):
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
