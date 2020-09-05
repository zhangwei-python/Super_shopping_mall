from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client
from rest_framework import serializers


class FastDFSStorage(Storage):
    def open(self, name, mode='rb'):
        # 如果需要把上传的文件存储django本地，则需要在本地打开一个文件
        return None # 把图片上传fdfs，不是保存本地
    def save(self, name, content, max_length=None):
        # 保存文件逻辑：把文件上传到fdfs服务器上
        conn=Fdfs_client('./shopping_mall/utils/fastdfs/client.conf')
        file_data=content.read()

        res=conn.upload_by_buffer(file_data)

        if res is None:
            raise serializers.ValidationError('上传fdfs失败！')
        file_id=res['Remote file_id']

        return file_id




    def url(self, name):
        # 该函数决定了，ImageField.url的结果
        # name: 当前字段在数据库中存储的值
        # name = group1/M00/00/02/CtM3BVrPB4GAWkTlAAGuN6wB9fU4220429
        # "http://image.meiduo.site:8888/" + name
        return settings.FDFS_URL + name