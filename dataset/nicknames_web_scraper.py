import os
import re
from collections import Counter
from itertools import chain
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd
import requests
import twint
from lxml import html
from tqdm import tqdm

from .utils import *
from config import *


def get_twitter_urls(category: str, min_no_of_users: int) -> List[str]:
    urls, page_no = list(), 0
    # I think it's the count of users per page, but not sure. Whatever, it's just for progress bar xD
    users_per_page = 20

    with tqdm(desc=f'Downloding page of {category}', total=int(np.ceil(min_no_of_users / users_per_page)), leave=False) as ubar:
        while len(urls) < min_no_of_users:
            page_no += 1
            page = requests.get(f'https://fanpagelist.com/category/{category}/view/list/sort/followers/page{page_no}')
            ubar.update(1)
            if not page.ok:
                break

            twitter_url_xpath = '//li[@class="ranking_results"]//a[@class="clicky_ignore"]/@href'
            tweeter_urls = html.fromstring(page.content).xpath(twitter_url_xpath)
            if not tweeter_urls:
                break
            urls.extend(tweeter_urls)
            ubar.set_postfix(len=len(urls))
    return urls


def add_nicknames_from_urls(urls: List[str], usernames: Dict[str, str], category: str):
    username_re = re.compile(r'.*screen_name=([\w\d-]+)')
    with tqdm(urls, desc='Extracting usernames', leave=False) as ubar:
        for url in ubar:
            matched = username_re.match(url)
            if not matched:
                continue
            matched = matched.group(1)
            usernames[category].append(matched)
            ubar.set_postfix(username=matched)


def download_category(*categories: List[str], min_no_of_users: int = 100) -> List[str]:
    usernames = {category: list() for category in categories}

    with tqdm(categories, desc='Getting category users', leave=False) as cbar:
        for group in cbar:
            cbar.set_postfix(group=group)
            urls = get_twitter_urls(group, min_no_of_users)
            if not urls:
                raise Exception(f'Cannot download html for category {group}')
            add_nicknames_from_urls(urls, usernames, group)

            with open(os.path.join(RAW_USERLISTS_FROM_PAGE, f'{group}.txt'), 'w') as f:
                f.write('\n'.join(usernames[group]))

    return {k: set(map(lambda elem: elem.lower(), v)) for k, v in usernames.items() if k in categories}


def find_categories_on_main_page(url: str) -> List[str]:
    tweeter_urls = html.fromstring(requests.get(url).content).xpath('//@href')
    cats = []
    for cat in tqdm(tweeter_urls, 'Extract categories', leave=False):
        matched = re.match(r'.*category/(.*)', cat)
        if not matched:
            continue
        matched = matched.groups()[0]
        cats.append(matched)
    return list(filter(lambda cat: not cat.startswith(r'top_users') and not re.findall('view', cat), cats))


def filter_and_export(categories: Sequence[str], groups: Dict[str, Set[str]]):
    try:
        politicians = load_userlist_from_file('politicians.txt', USERLISTS_HELPERS_DIR)
        politicians = set(map(lambda elem: elem.lower(), politicians))
        groups['politicians'].update(politicians)
        del politicians
    except FileNotFoundError as e:
        print(e)

    try:
        musicians = pd.read_csv(os.path.join(USERLISTS_HELPERS_DIR, 'musicians.csv'), header=0)
        musicians = musicians['Twitter handle'].astype(str)
        musicians = filter(lambda elem: elem != 'nan', musicians)
        musicians = set(map(lambda elem: str(elem[1:]).lower(), musicians))
        groups['musicians'].update(musicians)
        del musicians
    except FileNotFoundError as e:
        print(e)

    duplicated = get_duplicates_in_dict(groups)

    filtered_group = {}
    for group, users in tqdm(groups.items(), 'Filtering and exporting', leave=False):
        with open(os.path.join(USERS_LIST_DIR, f'{group}.txt'), 'w') as f:
            filtered_group[group] = set([user.lower() for user in users]) - duplicated
            f.write('\n'.join(filtered_group[group]))
    summary_dict(filtered_group, 'Summary')


def download_dataset(groups_names: Sequence[str] = GROUPS):
    groups = download_category(*groups_names)
    filter_and_export(groups_names, groups)
