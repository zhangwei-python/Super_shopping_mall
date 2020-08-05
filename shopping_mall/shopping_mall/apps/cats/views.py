import base64
import json
import pickle

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from goods.models import SKU


class CartsView(View):
    """购物车管理"""
    def get(self,request):
        """线上购物车"""
        if request.user.is_authenticated:
            #已登录用户,查询redis
            redis_conn=get_redis_connection('carts')
            #获取购物车数据
            item_dict=redis_conn.hgetall('carts_%s'%request.user.id)
            #获取选择状态\
            cart_selected=redis_conn.smembers('selected_%s'%request.user.id)
            cart_dict = {}
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }

        else:
            #未登录用户,查询cookie
            cookie_cart=request.COOKIES.get('carts')

            if cookie_cart:
                cart_dict=pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict={}

        sku_ids=cart_dict.keys()
        skus=SKU.objects.filter(id__in=sku_ids)
        cart_skus=[]
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': cart_dict.get(sku.id).get('selected'),
                'default_image_url': sku.default_image_url.url,
                'price': sku.price,
                'amount': sku.price * cart_dict.get(sku.id).get('count'),
            })
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'cart_skus':cart_skus
        })



    def post(self,request):
        """添加购物车"""
        #接收参数
        data=json.loads(request.body.decode())
        sku_id=data.get("sku_id")
        count=data.get('count')
        selected=data.get('selected')
        #校验参数
        if not all([sku_id,count]):
            return JsonResponse({
                'code':400,
                'errmsg':'缺少参数'
            })


        if request.user.is_authenticated:
            #用户登录,操作redis购物车
            redis_conn=get_redis_connection('carts')
            redis_conn.hincrby('carts_%s'%request.user.id,
                               sku_id,
                               count)
            if selected:#选中状态
                redis_conn.sadd('select_%s'%sku_id)
            return JsonResponse({
                'code':0,
                'errmsg':'添加购物车成功'
            })
        else:
            #未登录,操作cookie
            cookie_cart=request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict=pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict={}

            if sku_id in cart_dict:
                count+=cart_dict[sku_id]['count']

            cart_dict[sku_id]={
                'count':count,
                "selected":selected
            }
            cart_data=base64.b64encode(pickle.dumps(cart_dict)).decode()
            response=JsonResponse({
                'code':0,
                'errmsg':'添加购物成功'
            })

            response.set_cookie('carts',cart_data)

            return response



    def put(self,request):
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
        count=data.get('count')
        selected=data.get('selected')

        # 判断参数是否齐全
        if not all([sku_id, count]):
            return JsonResponse({'code':400,
                                       'errmsg': '缺少必传参数'})
            # 判断sku_id是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
                return JsonResponse({'code':400,
                                    'errmsg': 'sku_id不存在'})

        #判断用户是否登录
        user=request.user
        if user.is_authenticated:
            #用户已登录,修改redis
            redis_conn=get_redis_connection('carts')
            redis_conn.hset('carts_%s'%user.id,sku_id,count)
            if selected:
                redis_conn.sadd('selected_%s'%user.id,sku_id)
            else:
                redis_conn.srem('selected_%s'%user.id,sku_id)
            cart_sku={
                'id':sku_id,
                'count':count,
                'name':sku.name,
                'selected':selected,
                'default_image_url':sku.default_image_url.url,
                'price':sku.price,
                'amount':sku.price*count

            }
            return JsonResponse({
                'code':0,
                'errmsg':'修改购物车成功',
                'cart_sku':cart_sku
            })
        else:
            #未登录,操作cookie
            cookie_cart=request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict=pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict={}
            #接口采用幂等,直接覆盖
            cart_dict[sku_id]={
                'count':count,
                'selected':selected
            }
            cart_data=base64.b64encode(pickle.dumps(cart_dict)).decode()

            cart_sku={
                'id':sku_id,
                'count':count,
                'selected':selected
            }

            response=JsonResponse({
                'code':0,
                'errmsg':'修改购物车',
                'cart_sku':cart_sku
            })

            response.set_cookie('carts',cart_data)

            return response



    def delete(self,request):
        """删除购物车"""
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
        selected=data.get('selected')
        user=request.user

        if user.is_authenticated:
            #已登录用户
            redis_conn=get_redis_connection('carts')
            redis_conn.hdel('carts_%s'%user.id,sku_id)
            redis_conn.srem('selected_%s'%user.id,sku_id)
            return JsonResponse({
                'code':0,
                "errmsg":'删除购物车成功'
            })
        else:
            #未登录用户呢
            cookie_cart=request.COOKIES.get('carts')
            cart_dict={}
            if cookie_cart:
                cart_dict=pickle.loads(base64.b64decode(cookie_cart.encode()))

            response=JsonResponse({
                'code':0,
                'errmsg':'删除成功'
            })

            if sku_id in cart_dict:
                del cart_dict[sku_id]
                cart_data=base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts',cart_data)

            return response






class CartSelectAllView(View):
    """全选购物车"""

    def put(self,request):
        data=json.loads((request.body.decode()))
        selected=data.get('selected')

        #判断用户是否登录
        user=request.user
        if user.is_authenticated:
            #登录用户
            redis_conn=get_redis_connection('carts')
            item_dict=redis_conn.hgetall('carts_%s'%user.id)
            sku_ids=item_dict.keys()
            if selected:
                redis_conn.sadd("selected_%s"%user.id,*sku_ids)
            else:
                redis_conn.srem("selected_%s"%user.id,*sku_ids)

            return JsonResponse({
                'code':0,
                'errmsg':'全选购物车成功'
            })

        else:
            #未登录用户
            cookie_cart=request.COOKIES.get('carts')
            response=JsonResponse({
                'code':0,
                'errmsg':'全选购物车成功'
            })

            if cookie_cart:
                cart_dict=pickle.loads(base64.b64decode(cookie_cart.encode()))
                for sku_id in cart_dict.keys():
                    cart_dict[sku_id]['selected']=selected
                cart_data=base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts',cart_data)
            return response





class CartsSimpleView(View):
    """商品页面右上角购物车"""
    def get(self,request):

        user=request.user
        if user.is_authenticated:
            redis_conn=get_redis_connection('carts')
            item_dict=redis_conn.hgetall('carts_%s'%user.id)
            cart_selected=redis_conn.smembers('selected_%s'%user.id)
            cart_dict={}
            for sku_id,count in item_dict.items():
                cart_dict[int(sku_id)]={
                    'count':int(count),
                    'selected':sku_id in cart_selected
                }

        else:
            cookie_cart=request.COOKIES.get('carts')
            cart_dict={}
            if cookie_cart:
                cart_dict=pickle.loads(base64.b64decode(cookie_cart.encode()))

        #构造响应数据

        cart_skus=[]
        sku_ids=cart_dict.keys()
        skus=SKU.objects.filter(id__in=sku_ids)
        
        for sku in skus:
            cart_skus.append({
                'id':sku.id,
                'name':sku.name,
                'count':cart_dict.get(sku.id).get('count'),
                'default_image_url':sku.default_image_url.url

            })

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'cart_skus':cart_skus
        })


