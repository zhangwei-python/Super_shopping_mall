import json
import re

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from django_redis import get_redis_connection

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django import http
from django.views import View

from cats.utils import merge_cart_cookie_to_redis
from goods.models import SKU, GoodsVisitCount
from users.models import User, Address


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        '''判断用户名是否重复'''
        # 1.查询username在数据库中的个数
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'访问数据库失败'})

        # 2.返回结果(json) ---> code & errmsg & count
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count':count})

class MobileCountView(View):
    """判断手机号是否重复"""
    def get(self,request,mobile):
        count=User.objects.filter(mobile=mobile).count()
        return  JsonResponse({
            "code":0,
             "errms":'ok',
            'count':count
        })



#注册业务
class RegisterView(View):

    def post(self,request):
        #获取请求信息
        dict=json.loads(request.body.decode())

        username=dict.get("username")
        password=dict.get('password')
        password2=dict.get('password2')
        mobile=dict.get('mobile')
        sms_code=dict.get('sms_code')
        allow=dict.get('allow')

        #检验参数
        if not all([username,password,password2,mobile,sms_code,allow]):
            return JsonResponse({'code':400,'errmsg':'缺少参数'})

        if password != password2:
            return JsonResponse({'code':400,'errmsg':'密码输入不一致'})

        #短型验证码
        conn=get_redis_connection('verify_code')
        sms_code_server=conn.get("msg_%s"%mobile)

        if not sms_code_server:
            return JsonResponse({'code':400,'errmsg':'短信验证码失效'})
        #创建用户
        try:
            user=User.objects.create_user(username=username,password=password,mobile=mobile)
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'操作数据库失败'})

        login(request, user)

        return JsonResponse({'code':0,'errmsg':'ok'})







# 登录
class LoginView(View):
    """用户登录功能"""

    def post(self,request):
        #获取参数
        data=json.loads(request.body.decode())
        username=data.get('username')
        password=data.get('password')
        remembered=data.get('remembered')

        #校验参数
        if not all([username,password]):
            return JsonResponse({'code':400,'errmsg':'缺少必要参数'})
        #用户认证
        user=authenticate(username=username,password=password)
        print(user)
        if user is None:

            return JsonResponse({'code':400,'errmsg':"用户名或密码错误"})

        #状态保持
        login(request,user)

        #设置cookie时间
        if remembered:
            request.session.set_expiry(3600*24*24)
        else:
            request.session.set_expiry(None)

        response = JsonResponse({'code': 0,
                                'errmsg': 'ok'})
        response.set_cookie('username',
                                    user.username,
                                    max_age=3600*60*60)
        response = merge_cart_cookie_to_redis(request=request, user=user, response=response)
        return response







#退出登录
class LogoutView(View):
    def delete(self,request):

        logout(request)

        response=JsonResponse({'code':200,'errmsg':'ok'})
        #删除cookie
        response.delete_cookie('username')

        return response





class UserInfoView(View):
    "判断用户是否登录"
    def get(self,request):
        user=request.user
        if not user.is_authenticated:
            return JsonResponse({
               "code":400,
                "errmsg":"用户未登录"
            })
        else:
            return JsonResponse({
                "code":0,
                "errmsg":'ok',
                "info_data":{"username": user.username,
                            "mobile": user.mobile,
                            "email": user.email,
                             "email_active":user.email_active}
            })









class EmailView(View):

    """邮箱添加和发送邮件"""
    def put(self,request):
        #获取参数
        data=json.loads(request.body.decode())
        email=data.get('email')
        #检验参数
        if not email:
            return JsonResponse({
                'code':400,
                'errmsg':'缺少email'
            })
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            return JsonResponse({
                'code': 400,
                'errmsg': 'email格式错误'
            })

        #写入数据库
        user=request.user
        try:
            user.email=email
            user.save()
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '数据库操作失败'
            })


        #发送邮件
        verify_url=user.generate_verify_email_url()
        print(verify_url)
        send_mail(
            '超级商城验证',
            "",
            settings.EMAIL_FROM,
            [user.email],
            html_message='<a href="%s">%s</a>' % (verify_url,verify_url)
            #verify_url
        )

        return JsonResponse({
            'code': 0,
            'errmsg': '邮件发送成功'
        })



class VerifyEmailView(View):
    """邮箱验证激活"""
    def put(self,request):
        #获取数据
        token=request.GET.get('token')

        #参数校验
        if not token:
            return JsonResponse({
                'code':400,
                "errmsg":'缺少参数'
            })

        user=User.check_verify_email_token(token)
        if not user:
            return JsonResponse({
                'code':400,
                "errmsg":'验证失败'
            })
        #激活邮箱
        user.email_active=True
        user.save()


        return JsonResponse({
            "code":0,
            "errmsg":'邮箱激活成功'
        })






class CreateAddressView(View):
    """创建用户地址"""

    def post(self,request):
        #获取当前用户对象
        user=request.user

        #获取参数
        data=json.loads(request.body.decode())
        receiver=data.get('receiver')
        province_id=data.get('province_id')
        city_id=data.get('city_id')
        district_id=data.get('district_id')
        place=data.get('place')
        mobile=data.get('mobile')
        tel=data.get('tel')
        email=data.get('email')

        if not all([receiver,province_id,city_id,district_id,place,mobile]):
            return JsonResponse({
                'code':400,
                'errmsg':'缺少必填选项'
            })

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})
        #保存地址到数据库
        try:
            address=Address.objects.create(
                user=user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except:
            return JsonResponse({
                'code':400,
                'errmsg':'新加地址失败'
            })

        #换回前段数据
        address_data={
            "id":address.id,
            "title":address.title,
            'receiver':address.receiver,
            'province':address.province.name,
            'city':address.city.name,
            'district':address.district_id,
            'place':address.mobile,
            'mobile':address.mobile,
            'tel':address.tel,
            'email':address.email
        }

        return JsonResponse({
            'code':0,
            'errmsg':'添加地址成功',
            'address':address_data

        })

class AddressView(View):
    """展示收货地址"""
    def get(self,request):
        addresses=Address.objects.filter(user=request.user)
        address_list=[]

        for address in addresses:
            if address.is_deleted==False:
                address_dict={
                    "id":address.id,
                    'title':address.title,
                    'receiver':address.receiver,
                    'province':address.province.name,
                    "city": address.city.name,
                    "district": address.district.name,
                    "place": address.place,
                    "mobile": address.mobile,
                    "tel": address.tel,
                    "email": address.email
                }
            #设置默认地址首位
            if request.user.default_address_id==address.id:
                address_list.insert(0,address_dict)
            else:
                address_list.append(address_dict)


        default_id=request.user.default_address_id
        print(address_list)

        return JsonResponse({
             # 'code':0,
             # 'errmsg':'ok',
            'addresses':address_list,
            'default_address_id':default_id
        })



class UpdateDestroyAddressView(View):
    "修改收货地址"
    def put(self,request,address_id):
        #接收参数
        data = json.loads(request.body.decode())
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        #检验参数、
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})


        #跟新数据库
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except:
            return JsonResponse({
                'code':400,
                'errmsg':'数据更新失败'
            })


        #获取数据还回
        address=Address.objects.get(id=address_id)
        address_dict={
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'address':address_dict
        })

    def delete(self,request,address_id):
        """删除地址"""
        address=Address.objects.get(id=address_id)
        #逻辑删除
        try:
            address.is_deleted=True
            address.save()
        except:
            return JsonResponse({
                'code':400,
                'errmsg':'删除失败'
            })
        return JsonResponse({
            'code':0,
            'errmsg':'删除成功'
        })



class DefaultAddressView(View):
    """s设置默认地址"""
    def put(self,request,address_id):
        address=Address.objects.get(id=address_id)
        try:
            request.user.default_address=address
            request.user.save()
        except:
            return JsonResponse({
                'code':400,
                'errmsg':"设置默认失败"

            })

        return JsonResponse({
            'code':0,
            'errmsg':'设置成功'
        })


class UpdateTitleAddressView(View):
    """设置地址标题"""
    def put(self,request,address_id):
        data=json.loads(request.body.decode())
        title=data.get('title')
        try:
            address=Address.objects.get(id=address_id)
            address.title=title
            address.save()
        except:
            return JsonResponse({
                'code':400,
                'errmsg':'设置地址标题失败'
            })

        return JsonResponse({
            'code':0,
            'errmsg':'标题修改成功'
        })


class ChangePasswordView(View):
    "修改密码"
    def put(self,request):
        data=json.loads(request.body.decode())
        old_password=data.get('old_password')
        new_password=data.get('new_password')
        new_password2=data.get('new_password2')

        if not all([old_password,new_password,new_password2]):
            return ({
                'code':400,
                'errmsg':'缺少必要参数'
            })

        result=request.user.check_password(old_password)
        if not result:
            return JsonResponse({
                'code':400,
                'errmsg':'密码错误'
            })

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code': 400,
                                 'errmsg': '密码最少8位,最长20位'})

        if new_password != new_password2:
            return JsonResponse({'code': 400,
                                 'errmsg': '两次输入密码不一致'})
        try:
            request.user.set_password(new_password)
            request.user.save()
        except:
            return JsonResponse({
                "code":400,
                'errmsg':'密码修改失败'
            })
        logout(request)

        response=JsonResponse({
            'code':0,
            'errmsg':'密码修改成功'
        })
        response.delete_cookie('username')
        return response


class UserBrowseHistory(View):
    """用户浏览记录"""
    def get(self,request):
        redis_conn=get_redis_connection('history')
        sku_ids=redis_conn.lrange('history_%s'%request.user.id,0,-1)
        skus=[]
        for sku_id in sku_ids:
            sku=SKU.objects.get(id=int(sku_id))
            skus.append({
                'id':int(sku_id),
                'name':sku.name,
                'default_image_url':sku.default_image_url.url,
                'price':sku.price
            })

            return JsonResponse({
                'code':0,
                'errmsg':'ok',
                'skus':skus
            })



    def post(self,request):
        "保存用户浏览记录"
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')

        #查询
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':'sku不存在'
            })
        #保存到数据库
        redis_conn=get_redis_connection('history')
        user_id=request.user.id
        #去重
        redis_conn.lrem('history_%s'%user_id,0,sku_id)
        #存储
        redis_conn.lpush('history_%s'%user_id,sku_id)
        #保留5个
        redis_conn.ltrim('history_%s'%user_id,0,4)

        #补从：当前用户访问的sku的类别商品累加
        sku=SKU.objects.get(pk=sku_id)
        category=sku.category
        try:
            goods_visit=GoodsVisitCount.objects.get(
                category_id=category.id,
                create_time__gte=timezone.localtime().replace(hour=0,minute=0,second=0)
            )
        except Exception as e:
            GoodsVisitCount.objects.create(
                count=1,
                category=category
            )
        else:
            goods_visit.count+=1
            goods_visit.save()


        return JsonResponse({
            'code':0,
            'errmsg':'ok'
        })












