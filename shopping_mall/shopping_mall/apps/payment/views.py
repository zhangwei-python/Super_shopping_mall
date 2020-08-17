import os

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from orders.models import OrderInfo
from alipay import AliPay

from payment.models import Payment


class PaymentView(View):
    """订单支付功能"""
    def get(self,request,order_id):
        user=request.user
        try:
            order=OrderInfo.objects.get(order_id=order_id,
                                       )
        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':'order_id有误'
            })
        alipay=AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"keys/app_public_key.pem"),
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"keys/app_private_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        #生产支付宝链接
        order_string=alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=float(order.total_amount),
            subject="超级商城%s"%order_id,
            return_url=settings.ALIPAY_RETURN_URL

        )

        alipay_url=settings.ALIPAY_URL+"?"+order_string
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'alipay_url':alipay_url
        })


#
class PaymentStatusView(View):
    """保存订单结果"""
    def put(self,request):
        query_dict=request.GET
        data=query_dict.dict()
        signature=data.pop('sign')

        alipay=AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'keys/app_public_key.pem'),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG

        )
        success=alipay.verify(data,signature)

        if success:
            order_id=data.get('out_trade_no')
            trade_id=data.get('trade_no')

            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )

            #修改订单状态
            OrderInfo.objects.filter(
                order_id=order_id,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])

            return JsonResponse({
                'code':0,
                'errmsg':'ok',
                'trade_id':trade_id
            })
        else:
            return JsonResponse({
                'code':400,
                'errmsg':'非法请求'
            })


