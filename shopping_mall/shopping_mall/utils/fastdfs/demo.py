"""
如何使用fdfs客户端完成图片上传
"""

from fdfs_client.client import Fdfs_client

# 1、实例化fdfs对象
conn = Fdfs_client('./client.conf') # 接下来直接在demo.py所在目录下执行demo.py

# 2、在对象里面找方法实现上传图片

# 当前我们的图片并非保存在django本地，而是由浏览器传递过来的
# res = conn.upload_by_filename('/Users/weiwei/Desktop/images/1.jpg')
# res = conn.upload_by_file()

# 假设content是浏览器上传上来的文件数据
content = None
with open('/home/ubuntu/Picture/214x156c.jpg', 'rb') as f:
    content = f.read()

# Django后台调用此接口，把浏览器传来的文件数据传入，实现上传fdfs
res = conn.upload_by_buffer(content)

print("文件唯一标识: ", res['Remote file_id'])
