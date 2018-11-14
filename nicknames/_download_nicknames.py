import re
from collections import Counter
from itertools import chain
from typing import Dict, List

import numpy as np
import pandas as pd
import requests
import twint
from lxml import html
from tqdm import tqdm

from _download_celebrities import summary_dict, summary_html

__all__ = ['download_category', 'filter_and_export']


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
        for category in cbar:
            cbar.set_postfix(category=category)
            urls = get_twitter_urls(category, min_no_of_users)
            if not urls:
                raise Exception(f'Cannot download html for category {category}')
            add_nicknames_from_urls(urls, usernames, category)
    return {k: list(map(lambda elem: elem.lower(), v)) for k, v in usernames.items() if k in categories}


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


def filter_and_export(categories, groups):
    try:
        groups['politicians'].extend(map(lambda elem: elem.lower(), list(pd.read_csv('./adds/politicians.csv', header=0).screen_name)))
        groups['musicians'].extend(list(map(lambda elem: str(elem[1:]).lower(), filter(lambda elem: elem != 'nan', pd.read_csv('./adds/most_popular_musicians.csv', header=0)['Twitter handle'].astype(str)))))
    except FileNotFoundError as e:
        print(e)

    filtered_group = {}
    for group, users in tqdm(groups.items(), 'Filtering and exporting', leave=False):
        with open(f'{group}.txt', mode='w') as f:
            filtered_group[group] = set(users) - set(chain(*[v for k, v in groups.items() if k is not group]))
            f.write('\n'.join(filtered_group[group]))

    summary_dict(filtered_group, 'Summary')
