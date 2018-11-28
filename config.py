import os

GROUPS = ['musicians',
          'actors',
          'celebrities',
          'athletes',
          'politicians']

TEMP_DIR = '.tmp'
DATASET_DIR = 'dataset'
TWEETS_FILENAME = 'tweets.csv'
USERS_FILENAME = 'users.csv'

TWEETS_DIR = os.path.join(DATASET_DIR, 'tweets')
USERS_LIST_DIR = os.path.join(DATASET_DIR, 'users_lists')
RAW_USERLISTS_FROM_PAGE = os.path.join(USERS_LIST_DIR, 'raw')
USERLISTS_HELPERS_DIR = os.path.join(USERS_LIST_DIR, 'helpers')
FOLLOWERS_DIR = os.path.join(DATASET_DIR, 'followers')
HASHTAG_DIR = os.path.join(DATASET_DIR, 'hashtag')
