#  语雀笔记导出并自动发布到个人博客

## 环境
- python 3.10+
- 语雀API
- github
- hexo
- vercel

## 获取语雀指定库的笔记，下载并将图片上传到github图床，替换原始图片链接，并上传到hexo仓库，由vercel自动build发布

## 使用方法

1. 安装依赖
```
pip install -r requirements.txt
```

2. 配置config.py

```
TOKEN = 'your token'

# 语雀用户名
USERNAME = 'your username'

# 博客仓库名
BLOG_REPO = 'your blog repo'

# 博客仓库分支
BLOG_BRANCH = 'your blog branch'

# 博客仓库路径
BLOG_PATH = 'your blog path'
```

3. 运行脚本
```
python main.py
```

