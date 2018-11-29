import os
import shutil

from tqdm import tqdm

# tqdm.pandas()

GROUPS = ['musicians',
          'actors',
          'celebrities',
          'athletes',
          'politicians']

TWEETS_FILENAME = 'tweets.csv'
USERS_FILENAME = 'users.csv'
TEMP_DIR = '.tmp'
DATASET_DIR = 'dataset'
RESOURCE_DIR = 'res'

TWEETS_DIR = os.path.join(DATASET_DIR, 'tweets')
USERS_LIST_DIR = os.path.join(DATASET_DIR, 'users_lists')
RAW_USERLISTS_FROM_PAGE = os.path.join(USERS_LIST_DIR, 'raw')
USERLISTS_HELPERS_DIR = os.path.join(USERS_LIST_DIR, 'helpers')
FOLLOWERS_DIR = os.path.join(DATASET_DIR, 'followers')
HASHTAG_DIR = os.path.join(DATASET_DIR, 'hashtag')


def create_dir_if_not_exist(dir_path):
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
                 TEMP_DIR):
    create_dir_if_not_exist(dir_path)
