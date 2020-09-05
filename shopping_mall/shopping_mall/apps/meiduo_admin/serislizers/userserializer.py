import re

from rest_framework import serializers

from users.models import User


class UserModelSerializer(serializers.ModelSerializer):

    class Meta:
        model=User
        fields=["id",
                "username",
                "mobile",
                "email",
                "password"]
        extra_kwargs={
            "username":{'max_length':20,'min_length':5},
            "password":{"write_only":True}
        }
    def Validate_mobile(self,value):
            if not re.match(r'^1[3-9]\d{9}$',value):
                raise serializers.ValidationError('手机格式有误')
            return value


        #重写create来创建超级管理员
    def create(self,validated_data):


        return User.objects.create_superuser(**validated_data)

        # User.objects.create() --> 新建普通用户，切密码未加密
        # User.objects.create_user() --> 新建普通用户，密码加密
        # User.objects.create_superuser() --> 新建is_staff=True用户，密码加密