import os
from collections import defaultdict
from itertools import chain
from os.path import join as pj
from typing import Sequence

import numpy as np
import pandas as pd
from langdetect import detect_langs
from tqdm import tqdm

from config import TWEETS_DIR, TWEETS_FILENAME

from .scrappers import scrap_tweets
from .tweets_utils import preprocess_tweet

__all__ = ['only_lang_users']


def tweeter_user_lang_detect(user: str,
                             limit: int = 10,
                             csv_path: str = pj(TWEETS_DIR, TWEETS_FILENAME),
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
