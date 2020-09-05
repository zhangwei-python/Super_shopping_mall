from datetime import timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import GoodsVisitCount
from users.models import User
from django.utils import timezone

class UserTotalCountView(APIView):
    """用户总量"""
    def get(self,request):

        count=User.objects.all().count()

        date=timezone.localtime()

        return Response({
            'count':count,
            'date':date.date()
        })


class UserDayCountView(APIView):
    """日增用户"""
    def get(self,request):
        date_time=timezone.localtime()
        date_0_time=date_time.replace(hour=0,minute=0,second=0)

        count=User.objects.filter(date_joined__gte=date_0_time).count()

        return Response({
            'count':count,
            'date':date_0_time.date()
        })



class UserActiveCountView(APIView):
    """日活跃用户量"""

    def get(self,request):

        date_0_time=timezone.localtime().replace(hour=0,minute=0,second=0)
        count=User.objects.filter(last_login__gte=date_0_time).count()

        return Response({
            'count':count,
            'date':date_0_time.date()
        })




class UserOrderCountView(APIView):
    """日下单用户统计"""
    def get(self,request):
        date_0_time=timezone.localtime().replace(hour=0,minute=0,second=0)
        order_users=User.objects.filter(
            orders__create_time__gte=date_0_time
        )

        count=len(set(order_users))

        return Response({
            'count':count,
            'date':date_0_time.date()
        })



class UserMonthCountView(APIView):
    def get(self,request):
        #当日0时
        edn_0_time=timezone.localtime().replace(hour=0,minute=0,second=0)
        #开始0时
        start_0_time=edn_0_time-timedelta(days=29)
        #返回数据
        list=[]
        for index in range(30):
            date_time=start_0_time+timedelta(days=index)
            count=User.objects.filter(
                date_joined__gte=date_time,
                date_joined__lte=date_time+timedelta(days=1)
            ).count()
            list.append({
                'count':count,
                'date':date_time.date()
            })
        return Response(list)





from rest_framework.generics import ListAPIView
from meiduo_admin.serislizers.goodvisitserializer import GoodsVisitModelSerializer
class GoodsDayView(ListAPIView):
    """日商品类访问量"""
    queryset = GoodsVisitCount
    serializer_class = GoodsVisitModelSerializer

    def get_queryset(self):

        return self.queryset.objects.filter(
            update_time__gte=timezone.localtime().replace(hour=0,minute=0,second=0)
        )


