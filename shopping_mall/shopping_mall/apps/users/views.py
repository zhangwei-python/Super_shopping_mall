import json
import re

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login, authenticate, logout
from django_redis import get_redis_connection

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django import http
from django.views import View
from users.models import User

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
            '<p><a href="%s">%s<a></p>' % (verify_url,verify_url)
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










