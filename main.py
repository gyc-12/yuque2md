
import asyncio
import json
import os.path
import logging
import select
from urllib import parse
from prettytable import PrettyTable
from pyuque.client import Yuque
from huepy import *
from utils import download_md, get_docs, get_repos, is_dir_exists, make_dir, my_repo_list_docs

async def main():
    # 读取config.json
    with open('./config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        token = config['yuque_token']
        need_upload_github = config['need_upload_github']
    token = os.getenv("YUQUE_TOKEN")
    yuque = Yuque(token)
    Yuque.repo_list_docs = my_repo_list_docs
    base_dir = "./YuqueExport"
    if not is_dir_exists(base_dir):
     make_dir(base_dir)
  # 获取用户ID
    user_id = yuque.user.get()['data']['id']
    # 获取所有仓库
    all_repos = get_repos(user_id,yuque)
    repos_table = PrettyTable(["ID", "Name"])
    for repo_id, repo_name in all_repos.items():
        repos_table.add_row([repo_id, repo_name])
    print(repos_table)
    repo_id = input("请输入要导出的仓库ID:")
    selected_repo_name = all_repos[repo_id]
    all_docs = get_docs(repo_id,yuque)
    docs_table = PrettyTable(["ID", "Name"])
    for doc_id, doc_name in all_docs.items():
        docs_table.add_row([doc_id, doc_name])
    print(docs_table)
    doc_id = input("请输入要导出的文档ID(all为全部):")
    isall = doc_id.lower() == "all"
    if not isall:
        for doc_id, doc_name in all_docs.items():
            if doc_id == doc_id:
                doc_content = yuque.doc.get(doc_id)['data']['body']
                all_docs = [doc_id]
                break
    for doc_id, doc_title in all_docs.items():
        # 将不能作为文件名的字符进行编码
        for char in r'/\<>?:"|*':
            doc_title = doc_title.replace(char, parse.quote_plus(char))
        print(f"Get Doc {doc_title} ...")
        await download_md(repo_id, selected_repo_name, doc_id, doc_title,yuque,need_upload_github)

    

if __name__ == '__main__':
        asyncio.run(main())
        