import json
from _decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from django.views import View

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from users.models import Address

from django_redis import get_redis_connection


class OrderSettlementView(LoginRequiredMixin,View):
    """结算顶单"""

    def get(self,request):
        user=request.user
        #差选地址
        addresses=Address.objects.filter(user=request.user,

                                     is_deleted=False)

        #从购物车查找勾选商品
        redis_conn=get_redis_connection('carts')
        item_dict=redis_conn.hgetall('carts_%s'%user.id)
        cart_selected=redis_conn.smembers('selected_%s'%user.id)
        # cart={}
        # for sku_id in cart_selected:
        #     # cart[int(sku_id)]=int(item_dict[sku_id])
        #
        #     cart[sku_id] = int(item_dict[sku_id])
        #
        # #查询商品信息
        sku_list=[]
        # skus=SKU.objects.filter(id__in=cart.keys())
        # for sku in skus:
        #     sku_list.append({
        #         'id':sku.id,
        #         'name':sku.name,
        #         "default_image_url":sku.default_image_url.url,
        #         'count':cart[sku.id],
        #         'price':sku.price
        #     })

        for k, v in item_dict.items():
            # k:b'1'; v:b'4'
            if k in cart_selected:
                sku = SKU.objects.get(pk=k)
                sku_list.append({
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': sku.default_image_url.url,
                    'price': sku.price,
                    'count': int(v)
                })
        #运费
        freight=Decimal('10.00')

        #地址
        list=[]
        for address in addresses:
            list.append({
                'id':address.id,
                'province':address.province.name,
                'city':address.city.name,
                'place':address.place,
                'receiver':address.receiver,
                'mobile':address.mobile
            })
        #返回数据
        context={
            'addresses':list,
            'skus':sku_list,
            'freight':freight
        }


        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'context':context
        })




class OrderCommitView(View):
    '''订单提交'''
    def post(self,request):
        """保持订单信息"""
        data=json.loads(request.body.decode())
        address_id=data.get('address_id')
        pay_method=data.get('pay_method')
        #数据校验
        if not all([address_id,pay_method]):
            return JsonResponse({
                'code':400,
                'errmsg':'缺少必要参数'
            })
        try:
            address=Address.objects.get(pk=address_id)
        except Exception as e:
            return ({
                'code':400,
                'errmsg':'地址错误'
            })
        if pay_method not in [0,1]:
            return JsonResponse({
                'code':400,
                'errmsg':'不支持的付款方式'
            })

        user=request.user
        order_id=timezone.localtime().strftime("%Y%m%d%H%M%S")+"%09d"%user.id
        #保存顶单信息
        with transaction.atomic():
            save_id=transaction.savepoint()#事务执行保存点
            order=OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=0,
                total_amount=Decimal('0'),
                freight=Decimal('10.00'),
                pay_method=pay_method,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if
                pay_method==OrderInfo.PAY_METHODS_ENUM['ALIPAY']
                else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
            )

            #读取购物车被勾选商品
            redis_conn=get_redis_connection("carts")
            cart_dict=redis_conn.hgetall('carts_%s'%user.id)
            selected_redis=redis_conn.smembers('selected_%s'%user.id)
            carts={}
            for k,v in cart_dict.items():
                if k in selected_redis:
                    carts[int(k)] = int(v)

            #获取商品id
            sku_ids=carts.keys()

            #便利查询商品信息
            for sku_id in sku_ids:
                while True:
                    sku=SKU.objects.get(id=sku_id)
                    old_stock=sku.stock
                    old_sales=sku.sales
                    #判断库存
                    sku_count=carts[sku.id]
                    if sku_count > sku.stock:
                        transaction.savepoint_rollback(save_id) #回滚
                        return JsonResponse({
                            'code':400,
                            'errmsg':'库存不足'
                        })
                    #修改数据库
                    # sku.stock-=sku_count
                    # sku.sales+=sku_count
                    # sku.save()
                    new_stock=old_stock-sku_count
                    new_sales=old_sales+sku_count
                    result=SKU.objects.filter(id=sku.id,
                                              stock=old_stock,
                                              sales=old_sales).update(
                        stock=new_stock,sales=old_sales
                    )
                    if result==0:
                        continue
                    break

                #修改spu销量
                # sku.goods.sales+=sku_count
                # sku.goods.save()

                #保存订单商品信息
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=carts[sku_id],
                    price=sku.price
                )
                order.total_count+=sku_count
                order.total_amount+=(sku_count*sku.price)
            order.total_amount+=order.freight
            order.save()
            transaction.savepoint_commit(save_id)


        #清楚购物车结算商品
        redis_conn.hdel('carts_%s'%user.id,*selected_redis)
        redis_conn.srem('selected_%s'%user.id,*selected_redis)

        #返回响应
        return JsonResponse({
            'code':0,
            'errmsg':'下单成功',
            'order_id':order.order_id

        })

