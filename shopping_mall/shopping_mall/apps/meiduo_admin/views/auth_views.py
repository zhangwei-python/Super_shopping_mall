from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

from meiduo_admin.mypagination import Mypage
from meiduo_admin.serislizers.authserializer import *
class PermissionView(ModelViewSet):
    '权限管理'
    queryset = Permission.objects.all().order_by('id')
    serializer_class = PermissionSerializer
    pagination_class = Mypage

class ContentTypeView(ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = PermContentTypeSerializer


class GroupView(ModelViewSet):
    """用户组管理"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = Mypage

class CroupPermView(ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = GroupPermSerializer




class AdminView(ModelViewSet):
    "管理员用户"
    queryset = User.objects.filter(is_staff=True)
    serializer_class = AdminSerializer
    pagination_class = Mypage

class AdminGroupView(ListAPIView):
    queryset = Group.objects.all()
    serializer_class = AdminGroupSerializer