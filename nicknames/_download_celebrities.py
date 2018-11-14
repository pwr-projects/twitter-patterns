#!/bin/python
from typing import Sequence, Dict
import twint
import os
import pandas as pd
import shutil

__all__ = ['download_hashtags',
           'download_followers',
           'extract_tweet_authors',
           'get_users_with_lower_bound',
           'scrap_twits',
           'merge_with_scraped',
           'summary_html',
           'summary_dict']

def summary_html(summary: Dict[str, str], title: str) -> str:
    print(title)
    html = f'<table><tr><th>Category</th><th>Count</th></tr>'

    for k, v in summary.items():
        if len(v):
            html += f'<tr><td>{k}</td><td>{len(v)}</td></tr>'
            
    html += '</table>'
    return html


def summary_dict(summary: Dict[str, str], title: str):
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
    config.Search = ' '.join(hashtags)
    config.Lang = 'en'
    config.Store_csv = True
    config.Output = 'hashtags'
    config.User_full = True
    config.Followers = True
    config.Limit = tweets_limit
    config.Lowercase = True
    config.Verified = True
    twint.run.Search(config)


def scrap_twits(user: str, limit: int=100000):
    config = twint.Config()
    config.Username = user
    config.Limit = limit
    config.User_full = True
    config.User_info = True
    config.Followers = True
    config.Following = True
    config.Lowercase = True
    config.Profile = True
    config.Output = 'dataset'
    config.Store_csv = True
    config.Lang = 'en'
    twint.run.Search(config)


def download_followers(username: str):
    config = twint.Config()
    config.Username = username
    config.Lang = 'en'
    config.Store_csv = True
    config.Output = 'followers'
    config.Limit = 1
    config.Lowercase = True
    config.Hide_output = True
    twint.run.Followers(config)


def extract_tweet_authors() -> Sequence[str]:
    content = pd.read_csv('hashtags/tweets.csv', header=0)
    return content.username.unique()


def get_users_with_lower_bound(min_followers: int = 10000) -> Sequence[str]:
    assert min_followers > 0, 'min_followers should be greater than 0'
    content = pd.read_csv('followers/users.csv', header=0)[['username', 'followers']].drop_duplicates('username')
    return to_lower(content[content.followers > min_followers].username)

def merge_with_scraped(group_name: str, other_users: Sequence['str']):
    with open(f'{group_name}.txt', mode='r') as f:
        print(f'Merging nicks from group: {group_name}', end='...')
        new_users = set(map(lambda elem: elem.strip(), f.readlines()))
        new_users.update(set(other_users)) 
        print('OK')

    with open(f'{group_name}.txt', mode='w') as f:
        print(f'Saving to {group_name}.txt', end='...')
        f.write('\n'.join(new_users))
        print('OK')