from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Permission, ContentType, Group
from rest_framework import serializers

from users.models import User


class PermissionSerializer(serializers.ModelSerializer):
    "权限组管理"
    class Meta:
        model=Permission
        fields=[
            'id',
            'name',
            'codename',
            'content_type'

        ]

class PermContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model=ContentType
        fields=[
            'id',
            'name'
        ]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model=Group
        fields=[
            'id',
            'name',
            'permissions'
        ]

class GroupPermSerializer(serializers.ModelSerializer):
    class Meta:
        model=Permission
        fields=[
            'id',
            'name'
        ]




class AdminSerializer(serializers.ModelSerializer):
    """管理员用户"""
    class Meta:
        model=User
        fields=[
            'id',
            'username',
            'mobile',

            'password',
            'groups',
            'user_permissions'
        ]

        extra_kwargs={
            'password':{'write_only':True}
        }

    def validate(self, attrs):
        password=attrs.get('password')
        attrs['password']=make_password(password)
        attrs['is_staff']=True
        return attrs


class AdminGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model=Group
        fields=[
            'id',
            'name'
        ]