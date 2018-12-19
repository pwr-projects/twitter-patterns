import os
import shutil
from os.path import join as pj

from tqdm import tqdm


GROUPS = ['musicians',
          'actors',
          'athletes',
          'politicians']

TWEETS_FILENAME = 'tweets.csv'
USERS_FILENAME = 'users.csv'
FEATURES_FILENAME = 'twitter_patterns.csv'
FEATURES_INC_GRAPH_FILENAME = 'twitter_patterns_graph.csv'

TEMP_DIR = '.tmp'
DATASET_DIR = 'dataset'
RESOURCE_DIR = 'res'

TWEETS_DIR = pj(DATASET_DIR, 'tweets')
USERS_LIST_DIR = pj(DATASET_DIR, 'users_lists')
RAW_USERLISTS_FROM_PAGE = pj(USERS_LIST_DIR, 'raw')
USERLISTS_HELPERS_DIR = pj(USERS_LIST_DIR, 'helpers')
FOLLOWERS_DIR = pj(DATASET_DIR, 'followers')
HASHTAG_DIR = pj(DATASET_DIR, 'hashtag')
FEATURES_DIR = pj(DATASET_DIR, 'processed_features')


def only_classified_users_str(itis: bool) -> str:
    return 'inside' if itis else 'outside'


def create_dir_if_not_exist(dir_path: str):
    if not os.path.isdir(dir_path):
        print(f'Creating {dir_path}...')
        os.makedirs(dir_path)


for dir_path in (TWEETS_DIR,
                 USERS_LIST_DIR,
                 RAW_USERLISTS_FROM_PAGE,
                 USERLISTS_HELPERS_DIR,
                 FOLLOWERS_DIR,
                 HASHTAG_DIR,
                 RESOURCE_DIR,
                 TEMP_DIR,
                 FEATURES_DIR):
    create_dir_if_not_exist(dir_path)
