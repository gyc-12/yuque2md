"""
此模块包含各种实用函数和工具。

这些函数可以在项目的不同部分中使用，以执行常见任务和操作。
"""

import hashlib
import os.path
import logging
from pyuque.client import Yuque
import re
from huepy import *
from prettytable import PrettyTable
import functools
import asyncio
import aiohttp
from urllib import parse

from githubClient import GithubClient

# yuque = Yuque("token")

yq_headers = None
yq_base_url =  "https://www.yuque.com/api/v2/{}"
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
origin_md_dir = os.path.join(base_dir, "origin_md")
count = 0
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_dir_exists(dir_path):
    """
    检查目录是否存在。

    参数:
    dir_path (str): 要检查的目录路径。

    返回:
    bool: 如果目录存在则返回 True，否则返回 False。
    """
    return os.path.exists(dir_path) and os.path.isdir(dir_path)

def create_dir(dir_path):
    """
    创建目录。     

    参数:
    dir_path (str): 要创建的目录路径。
    """
    if not is_dir_exists(dir_path):
        os.makedirs(dir_path)

def write_text_to_file(file_path, text, encoding="utf-8", mode="w+", newline="\n"):
    """
    将文本写入文件。

    参数:
    file_path (str): 要写入的文件路径。
    text (str): 要写入的文本。
    encoding (str): 编码格式，默认为 "utf-8"。
    mode (str): 文件打开模式，默认为 "w+"。
    newline (str): 行结束符，默认为 "\n"。
    """
    try:
        with open(file_path, mode, encoding=encoding, newline=newline) as file:
            file.write(text+newline)
    except Exception as e:
        logging.error(f"写入文件失败: {e}")
# 知识库

class YuqueRepo:
     def __init__(self, repo_id, repo_type, repo_slug, repo_name, repo_namespace):
        self.repo_id = repo_id
        self.repo_ype = repo_type
        self.repo_slug = repo_slug
        self.repo_name = repo_name
        self.repo_namespace = repo_namespace
# 目录
class Catalog_Node:
    def __init__(self, node_type, node_title, node_uuid, parent_uuid, doc_id, repo_id, repo_name):
        self.node_type = node_type
        self.node_title = node_title
        self.node_uuid = node_uuid
        self.parent_uuid = parent_uuid
        self.child_node_list = []
        self.doc_id = doc_id
        self.repo_id = repo_id
        self.repo_name = repo_name
# 文档
class Doc:
    def __init__(self, doc_id, book_id, book_name, doc_slug, doc_title, doc_content):
        self.doc_id = doc_id
        self.book_id = book_id
        self.book_name = book_name;
        self.doc_slug = doc_slug
        self.doc_title = doc_title
        self.doc_content = doc_content

    def save_to_md(self):
        save_path = "{}{}{}{}{}.md".format(origin_md_dir, os.path.sep, self.book_name, os.path.sep,
                                           self.doc_title)
        print(save_path)
# 指定id获取仓库列表
def get_repos(user_id,yuque:Yuque):
    repos ={}
    for repo in yuque.user_list_repos(user_id)["data"]:
        repo_id = str(repo["id"])
        repo_name = repo["name"]
        repos[repo_id] =repo_name
    return repos
# 获取指定仓库下的文档列表
def get_docs(repo_id,yuque:Yuque):
    docs ={}
    for doc in yuque.repo_list_docs(repo_id)["data"]:
        doc_id = str(doc["id"])
        doc_title = doc["title"]
        docs[doc_id] = doc_title
    return docs
# 获取文档Markdown代码
def get_body(repo_id, doc_id,yuque:Yuque):
    doc = yuque.doc_get(repo_id, doc_id)

    body = doc['data']['body']
    body = re.sub("<a name=\"(\w.*)\"></a>", "", body)                 # 正则去除语雀导出的<a>标签
    body = re.sub(r'\<br \/\>', "\n", body)                            # 正则去除语雀导出的<br />标签
    # 第一步：处理 <br /> 后面紧跟着的 ![image.png]
    body = re.sub(r'<br\s*/>\s*(\!\[image\.png\])', r'\n\1', body)
    
    # 第二步：处理 ) 后面的 <br />，但不影响图片链接之间的 <br />
    body = re.sub(r'\)(<br\s*/>)(?!\s*\!\[)', r')\n', body)
    
    # 第三步：处理连续的图片链接，在它们之间添加换行符
    body = re.sub(r'(\)\s*)(?=\!\[image\.png\])', r'\1\n', body)
    body = re.sub(r'png[#?](.*)+', 'png)', body)                       # 正则去除语雀图片链接特殊符号后的字符串
    body = re.sub(r'jpeg[#?](.*)+', 'jpeg)', body)                     # 正则去除语雀图片链接特殊符号后的字符串
    return body
# 解析文档Markdown代码
async def download_md(repo_id, repo_name, doc_id, doc_title,yuque:Yuque,need_upload_github:bool):
    body = get_body(repo_id, doc_id,yuque)

    # 创建文档目录及存放资源的子目录
    repo_dir = os.path.join(base_dir, repo_name)
    make_dir(repo_dir)
    assets_dir = os.path.join(repo_dir, "assets")
    make_dir(assets_dir)
    print(body)

    # 保存图片
    pattern_images = r'(\!\[(.*)\]\((https:\/\/cdn\.nlark\.com\/yuque.*\/(\d+)\/(.*?\.[a-zA-z]+)).*\))'
    images = [index for index in re.findall(pattern_images, body)]
    if images:
        for index, image in enumerate(images):
            image_body = image[0]                                # 图片完整代码
            image_url = image[2]                                 # 图片链接
            image_suffix = image_url.split(".")[-1]              # 图片后缀
            local_abs_path = f"{assets_dir}/{doc_title}-{str(index)}.{image_suffix}"                # 保存图片的绝对路径
            doc_title_temp = doc_title.replace(" ", "%20").replace("(", "%28").replace(")", "%29")  # 对特殊符号进行编码
            local_md_path = f"![{doc_title_temp}-{str(index)}](assets/{doc_title_temp}-{str(index)}.{image_suffix})"  # 图片相对路径完整代码
            
            await download_images(image_url, local_abs_path)     # 下载图片
            # todo
            # 图片上传到github图床
            # 上传到github
            # 替换图片链接
            if need_upload_github:
                git_url =await upload_to_github(image_url)
                body = body.replace(image_url, git_url)
            else:
                body = body.replace(image_body, local_md_path)       # 替换链接
         

    # 保存附件
    pattern_annexes = r'(\[(.*)\]\((https:\/\/www\.yuque\.com\/attachments\/yuque.*\/(\d+)\/(.*?\.[a-zA-z]+)).*\))'
    annexes = [index for index in re.findall(pattern_annexes, body)]
    if annexes:
        for index, annex in enumerate(annexes):
            annex_body = annex[0]                                # 附件完整代码 [xxx.zip](https://www.yuque.com/attachments/yuque/.../xxx.zip)
            annex_name = annex[1]                                # 附件名称 xxx.zip
            annex_url = re.findall(r'\((https:\/\/.*?)\)', annex_body)                # 从附件代码中提取附件链接
            annex_url = annex_url[0].replace("/attachments/", "/api/v2/attachments/") # 替换为附件API
            local_abs_path = f"{assets_dir}/{annex_name}"           # 保存附件的绝对路径
            local_md_path = f"[{annex_name}](assets/{annex_name})"  # 附件相对路径完整代码
            await download_annex(annex_url, local_abs_path)         # 下载附件
            body = body.replace(annex_body, local_md_path)          # 替换链接

    # 保存文档
    markdown_path = f"{repo_dir}/{doc_title}.md"
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(body)

    # 建立文档索引
    # 对索引文档标题中的特殊符号进行编码
    doc_title_temp = doc_title.replace(" ","%20").replace("(","%28").replace(")","%29")
    record_doc_file = os.path.join(base_dir, f"{repo_name}.md")
    record_doc_output = f"- [{doc_title}](./{repo_name}/{doc_title_temp}.md) \n"
    with open(record_doc_file, "a+") as f:
        f.write(record_doc_output)

# 下载图片
async def download_images(image, local_name):
    logging.info(good(f"Download {local_name} ..."))
    async with aiohttp.ClientSession() as session:
        async with session.get(image) as resp:
            with open(local_name, "wb") as f:
                f.write(await resp.content.read())


# 下载附件
async def download_annex(annex, local_name):
    logging.info(good(f"Download {local_name} ..."))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "X-Auth-Token": token
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(annex, headers=headers) as resp:
            with open(local_name, "wb") as f:
                f.write(await resp.content.read())

# 创建目录
def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(info(f"Make Dir {path} ..."))
# 扩展函数
@functools.wraps(Yuque.repo_list_docs)
def my_repo_list_docs(self, namespace_or_id):
    offset = 0
    data_total = 0
    data_all = []
    while True:
        params = {
            "offset": offset,
            "limit": 100
        }
        result = self.send_request('GET', '/repos/%s/docs' % namespace_or_id.strip('/'), params=params)
        data = result["data"]
        data_all.extend(data)
        data_total += result["meta"]["total"]
 
        if len(data) < 100:
            break
        else:
            offset += 100
    # {'meta': {'total': 10}, 'data': []}
    my_dict = {
        'meta': {'total': data_total},
        'data': data_all
        }
    return my_dict
async def upload_to_github(url):
    config = {
        'bucket': 'your-repo-name',
        'prefix_key': 'images',
        'host': 'https://cdn.jsdelivr.net'
    }
    client = GithubClient.get_instance(config)
    uniqueId =  generateUniqueId(url)
    fullName = uniqueId + "." + url.split(".")[-1]
    # 检查图片是否存在
    image_url = client.has_image(fullName)
    if image_url:
        print(f"图片已存在: {image_url}")
        return image_url
    else:
        print("图片不存在")

    # 上传图片
    img_buffer =await getPicBufferFromURL(url)
    uploaded_url = client.upload_img(img_buffer,fullName)
    if uploaded_url:
        print(f"图片上传成功: {uploaded_url}")
        return uploaded_url
    else:
        print("图片上传失败")
        return None

# 根据url生成唯一文件名
def generateUniqueId(url):
    hash = hashlib.md5()
    hash.update(url.encode('utf-8'))
    return hash.hexdigest()

async def getPicBufferFromURL(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.content.read()