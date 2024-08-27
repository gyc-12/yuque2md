
import os.path
import logging
from prettytable import PrettyTable
from pyuque.client import Yuque

from utils import get_repos, is_dir_exists, make_dir, my_repo_list_docs



if __name__ == '__main__':
    token = ""
    yuque = Yuque(token)
    Yuque.repo_list_docs = my_repo_list_docs
    base_dir = "./YuqueExport"
    if not is_dir_exists(base_dir):
     make_dir(base_dir)
  # 获取用户ID
    user_id = yuque.user.get()['data']['id']
    # 获取所有仓库
    all_repos = get_repos(user_id)
    repos_table = PrettyTable(["ID", "Name"])
    for repo_id, repo_name in all_repos.items():
        repos_table.add_row([repo_id, repo_name])
    print(repos_table)


    
