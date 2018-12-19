import os
from collections import Counter
from itertools import chain
from os.path import join as pj
from subprocess import check_output
from typing import Dict, List, Sequence, Set

import pandas as pd
from tqdm import tqdm

from config import (FOLLOWERS_DIR, GROUPS, HASHTAG_DIR,
                    RAW_USERLISTS_FROM_PAGE, TEMP_DIR, TWEETS_DIR,
                    TWEETS_FILENAME, USERLISTS_HELPERS_DIR, USERS_FILENAME,
                    USERS_LIST_DIR)


def wc(filename):
    return int(check_output(['wc', '-l', filename]).split()[0])


def get_batch(groups_users: Dict[str, Set[str]],
              group_name: str,
              batch_size: int,
              batch_idx: int) -> List[str]:
    data = list(groups_users[group_name])
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


def summary_dict(groups_users: Dict[str, Set[str]], title: str):
    print(title)
    format = '{:15s}\t{:5d}'
    print('{:15s}\t{:5s}'.format('Group name', 'Count'))

    for k, v in groups_users.items():
        if len(v):
            print(format.format(k, len(v)))


def lower_list_of_strs(strs: Sequence['str']) -> List[str]:
    return list(map(lambda elem: elem.lower(), strs))


def get_duplicates_in_dict(groups_users: Dict[str, Set[str]],
                           other_users: Sequence[str] = []) -> Set[str]:
    return set(k for k, v in Counter(chain(*groups_users.values(), other_users)).items() if v > 1)


def add_not_duplicates(groups_users: Dict[str, Set[str]],
                       group_name: str,
                       users: Sequence[str]) -> Dict[str, Set[str]]:
    to_add = set(users) - get_duplicates_in_dict(groups_users, users)
    groups_users[group_name].update(to_add)
    return groups_users


def create_group_dict_from_userlists(userlist_dir: str = USERS_LIST_DIR) -> Dict[str, Set[str]]:
    groups = {}

    for group_name in tqdm(GROUPS, 'Reading group file'):
        with open(pj(USERS_LIST_DIR, f'{group_name}.txt'), mode='r') as f:
            users = set(map(lambda elem: elem.strip(), f.readlines()))

        groups[group_name] = users

    return groups


def export_users_dict_to_files(groups_users: Dict[str, Set[str]],
                               outdir: str = TEMP_DIR):
    for group_name, users in groups_users.items():
        outpath = f'{group_name}.txt'

        with open(outpath, mode='w') as f:
            f.write('\n'.join(users))


def merge_with_scraped(group_name: str, other_users: Sequence['str']) -> Dict[str, Set[str]]:
    groups_users = create_group_dict_from_userlists(RAW_USERLISTS_FROM_PAGE)
    groups_users = add_not_duplicates(groups_users, group_name, other_users)
    export_users_dict_to_files(groups_users)
    return groups_users
