import os
import requests
import base64
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GithubClient:
    def __init__(self, config):
        self.config = config
        self.username = os.getenv("GITHUB_USERNAME")
        self.secret_key = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO")
        self.init()

    def init(self):
        if not self.config.get('host'):
            logging.warning('未指定加速域名，将使用默认域名：https://raw.githubusercontent.com')
        
        if self.config.get('host') and 'cdn.jsdelivr.net' in self.config['host']:
            self.config['host'] = 'https://cdn.jsdelivr.net'
            logging.info(f"图床域名：{self.config['host']}")
    @classmethod
    def get_instance(cls, config):
        if not hasattr(cls, 'instance'):
            cls.instance = cls(config)
        return cls.instance
    def _fetch(self, method, file_name, base64_file=None):
        path = f"https://api.github.com/repos/{self.username}/{self.repo}/contents/{self.config['prefix_key']}/{file_name}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'yuque-hexo',
            'Authorization': f"token {self.secret_key}"
        }
        data = None
        if method == 'PUT':
            data = {
                'message': 'yuque-hexo upload images',
                'content': base64_file
            }

        try:
            response = requests.request(method, path, json=data, headers=headers, timeout=60)
            
            if response.status_code == 409:
                logging.warning('由于github并发问题，图片上传失败')
                return ''
            
            if response.status_code in [200, 201]:
                if self.config.get('host'):
                    return f"{self.config['host']}/gh/{self.username}/{self.repo}/{self.config['prefix_key']}/{file_name}"
                if method == 'GET':
                    return response.json()['download_url']
                return response.json()['content']['download_url']
            
            if method == 'PUT':
                logging.warning(f"请求图片失败，请检查: {response.text}")
            return ''
        except Exception as e:
            logging.warning(f"请求图片失败，请检查: {str(e)}")
            return ''

    def has_image(self, file_name):
        try:
            return self._fetch('GET', file_name)
        except Exception as e:
            logging.warning(f"检查图片信息时出错: {str(e)}")
            return ''

    def upload_img(self, img_buffer, file_name):
        try:
            base64_file = base64.b64encode(img_buffer).decode('utf-8')
            img_url = self._fetch('PUT', file_name, base64_file)
            if img_url:
                return img_url
        except Exception as e:
            logging.warning(f"上传图片失败，请检查: {str(e)}")
        return None

# 使用示例
if __name__ == "__main__":
    config = {
        'bucket': 'your-repo-name',
        'prefix_key': 'images',
        'host': 'https://cdn.jsdelivr.net'
    }
    client = GithubClient.get_instance(config)
    
    # 检查图片是否存在
    image_url = client.has_image('example.jpg')
    if image_url:
        print(f"图片已存在: {image_url}")
    else:
        print("图片不存在")

    # 上传图片
    with open('output/hexo/assets/12-0.png', 'rb') as f:
        img_buffer = f.read()
    uploaded_url = client.upload_img(img_buffer, 'new_image.jpg')
    if uploaded_url:
        print(f"图片上传成功: {uploaded_url}")
    else:
        print("图片上传失败")