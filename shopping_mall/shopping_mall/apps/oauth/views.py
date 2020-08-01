import json
import re

from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import render
from django_redis import get_redis_connection

from oauth.models import OAuthQQUser

# Create your views here.
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from itsdangerous import TimedJSONWebSignatureSerializer

from users.models import User


def generate_access_token(openid):
    """对openid加密"""
    se=TimedJSONWebSignatureSerializer(secret_key=settings.SECRET_KEY,
                                       expires_in=600)
    token=se.dumps({'openid':openid})
    return token.decode()

def check_access_token(access_token):
    """解码openid"""
    se=TimedJSONWebSignatureSerializer(secret_key=settings.SECRET_KEY,
                                       expires_in=600)
    try:
        data=se.loads(access_token)
    except:
        return None
    return data.get('openid')





class QQFirstView(View):
    """提供qq登录网址"""
    def get(self,request):
        #提去参数
        next_url=request.GET.get('next')
        #创建oauthqq对象
        oauth=OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=next_url
        )
        login_url=oauth.get_qq_url()

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            "login_url":login_url
        })


class QQUserView(View):
    """扫码登录回调处理"""
    def get(self,request):
        #获取code
        code=request.GET.get('code')
        if not code:
            return JsonResponse({
                'code':400,
                'errmsg':'缺少参数',

            })
        #创建oauth对象
        oauth=OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI
        )
        try:
            access_token=oauth.get_access_token(code)
            openid=oauth.get_open_id(access_token)
        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':'认证失败'
            })

        try:
            oauth_qq = OAuthQQUser.objects.get(openid=openid)
        except Exception as e:
            print(e)            #未绑定
            access_token=generate_access_token(openid)
            return JsonResponse({
                'code':300,
                'errmsg':'ok',
                'access_token':access_token
            })

        else:
            #绑定
            user=oauth_qq.user
            login(request,user)

            response=JsonResponse({
                'code':0,
                'errmsg':'qq登录成功'
            })
            #设置cookie
            response.set_cookie('username',user.username,max_age=3600*24*14)

            return response



    def post(self,request):
        """绑定用户"""
        #获取参数
        data=json.loads(request.body.decode())
        mobile=data.get('mobile')
        password=data.get('password')
        sms_code_client=data.get('sms_code')
        access_token=data.get('access_token')

        #参数校验
        if not all([mobile,password,sms_code_client,access_token]):
            return JsonResponse({
                'code':400,
                'errmsg':'缺少比传参数'
            })

            # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                     'errmsg': '请输入正确的手机号码'})

            # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'code': 400,
                                     'errmsg': '请输入8-20位的密码'})
        #判断短信验证码是否一致
        conn=get_redis_connection('verify_code')
        sms_code=conn.get('msg_%s'%mobile).decode()

        if not sms_code:
            return JsonResponse({
                'code':400,
                'errmsg':'短信验证码过期'
            })
        if sms_code_client != sms_code:
            return JsonResponse({
                'code':400,
                'errmsg':'短信验证吗错误'
            })

        #校验tokenid
        openid=check_access_token(access_token)
        if not openid:
            return JsonResponse({
                'code':400,
                'errmsg':'未获取openid'
            })

        #保存注册数据
        try:
            user=User.objects.get(mobile=mobile)
        except:
            user=User.objects.create_user(username=mobile,
                                          password=password,
                                          mobile=mobile)

        else:
            if not user.check_password(password):
                return JsonResponse({
                    'code':400,
                    'errmsg':'输入密码不正确'
                })

        #绑定openid
        try:
            OAuthQQUser.objects.create(openid=openid,
                                       user=user)
        except:
            return JsonResponse({
                'code':400,
                'errmsg':'数据库操作失败'
            })
        login(request,user)

        response=JsonResponse({
            'code':0,
            'errmsg':'ok'
        })
        response.set_cookie('username',user.username,max_age=3600*24*14)
        return response


