from rest_framework.viewsets import ModelViewSet

from meiduo_admin.mypagination import Mypage
from meiduo_admin.serislizers.order_serializer import *


class OrderView(ModelViewSet):
    queryset = OrderInfo.objects.all()
    serializer_class = OrderSerializer
    pagination_class = Mypage

    def get_queryset(self):
        keyword=self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(order_id__contains=keyword)
        return self.queryset.all()

    def get_serializer_class(self):

        if self.action=='list':
            return self.serializer_class
        elif self.action=="retrieve":
            return OrderDetailSerializer
        elif self.action=='partial_update':
            return OrderDetailSerializer
