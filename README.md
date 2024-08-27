#  语雀笔记导出并自动发布到个人博客

## 环境
- python 3.10+
- 语雀API
- github
- hexo
- vercel

## 处理流程
mermaid
graph TD
A[开始] --> B[获取语雀指定库的笔记]
B --> C[下载笔记中的图片]
C --> D[上传图片到GitHub图床]
D --> E[替换笔记中的原始图片链接]
E --> F[上传处理后的笔记到Hexo仓库]
F --> G[Vercel自动构建]
G --> H[发布网站]
H --> I[结束]

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

