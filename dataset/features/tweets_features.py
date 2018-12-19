import copy
import os
from ast import literal_eval
from os.path import join as pj

import emoji
import nltk
import numpy as np
import pandas as pd
from IPython.display import HTML, display
from polyglot.text import Text
from tqdm._tqdm_notebook import tqdm_notebook as tqdm

import dataset.tweets_utils as utils
from config import GROUPS, TWEETS_DIR, FEATURES_DIR

tqdm.pandas()

def tweets_features():
    for group_name in GROUPS:
        tweets_path = pj(TWEETS_DIR, f'{group_name}.csv')

        df = pd.read_csv(tweets_path, engine='python')

        df.dropna(subset=['tweet', 'mentions', 'hashtags', 'urls', 'photos'], inplace=True)
        cleaner = utils.TweetCleaner()

        df['temp_emotional_tweet'] = df.progress_apply(lambda tweet: cleaner.emotional_clean(tweet.tweet), axis=1)
        df['temp_clean_tweet'] = df.progress_apply(lambda tweet: [word for word in tweet.temp_emotional_tweet
                                                                if word not in emoji.UNICODE_EMOJI], axis=1)

        df['tp_author'] = df.progress_apply(lambda tweet: tweet.username, axis=1)
        df['tp_date'] = df.progress_apply(lambda tweet: tweet.date, axis=1)

        df['tp_tweet_len'] = df.progress_apply(lambda tweet: len(tweet.tweet), axis=1)
        df['tp_clean_tweet_len'] = df.progress_apply(lambda tweet: len(' '.join(tweet.temp_clean_tweet)), axis=1)

        df['tp_sentiment'] = df.progress_apply(lambda tweet: np.mean([word.polarity
                                                                    for word in Text(' '.join(tweet.temp_clean_tweet), 'en').words])
                                            if tweet.temp_clean_tweet else 0, axis=1)

        df['tp_emojis_num'] = df.progress_apply(lambda tweet: len([word for word in tweet.temp_emotional_tweet
                                                                if word in emoji.UNICODE_EMOJI]), axis=1)
        df['tp_mentions_num'] = df.progress_apply(lambda tweet: len(literal_eval(tweet.mentions)), axis=1)
        df['tp_hashtags_num'] = df.progress_apply(lambda tweet: len(literal_eval(tweet.hashtags)), axis=1)

        df['tp_has_url'] = df.progress_apply(lambda tweet: bool(len(literal_eval(tweet.urls))), axis=1)
        df['tp_has_image'] = df.progress_apply(lambda tweet: bool(len(literal_eval(tweet.photos))), axis=1)

        df['tp_has_gif'] = df.progress_apply(lambda tweet: not pd.isnull(tweet.gif_url), axis=1)
        df['tp_has_video'] = df.progress_apply(lambda tweet: not pd.isnull(tweet.video_url), axis=1)
        df['tp_has_place'] = df.progress_apply(lambda tweet: not pd.isnull(tweet.place), axis=1)

        df['tp_replies_count'] = df.progress_apply(lambda tweet: tweet.replies_count, axis=1)
        df['tp_retweets_count'] = df.progress_apply(lambda tweet: tweet.retweets_count, axis=1)
        df['tp_likes_count'] = df.progress_apply(lambda tweet: tweet.likes_count, axis=1)

        df['tp_is_retweet'] = df.progress_apply(lambda tweet: tweet.username != tweet.scraped_user, axis=1)
        df['tp_is_reply'] = df.progress_apply(lambda tweet: bool(tweet.is_reply_to), axis=1)
        df['tp_is_quote'] = df.progress_apply(lambda tweet: bool(tweet.is_quote_status), axis=1)

        df['tp_group'] = df.progress_apply(lambda tweet: tweet.group, axis=1)

        cols_to_rm = [c for c in df.columns if not c.startswith('tp_')]
        final_df = df.drop(cols_to_rm, axis=1)

        with pd.option_context('display.max_rows', 500, 'display.max_columns', 50, 'display.max_colwidth', -1):
            display(final_df)

        filename = f'{group_name}_twitter_posts.csv'
        final_df.to_csv(pj(FEATURES_DIR, filename), encoding='utf-8', index=False)