from rest_framework.generics import ListAPIView, CreateAPIView

from meiduo_admin.mypagination import Mypage
from users.models import User
from meiduo_admin.serislizers.userserializer import UserModelSerializer




class UserView(ListAPIView,CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    pagination_class = Mypage#制定分页器

    def get_queryset(self):
        keyword=self.request.query_params.get('keyword')

        if not keyword:
            return self.queryset.filter(
                is_staff=True
            )
        else:
            return self.queryset.filter(
                is_staff=True,
                username__contains=keyword
            )