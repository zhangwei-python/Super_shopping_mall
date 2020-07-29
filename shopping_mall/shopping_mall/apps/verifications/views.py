import random

from django_redis import get_redis_connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from shopping_mall.libs.captcha.captcha import captcha
from shopping_mall.libs.yuntongxun.sms import CCP

from celery_tasks.msg.tasks import ccp_send_msg_code

# hs, text, image = captcha.generate_captcha()
# print(hs,text,image)

class ImageCodeView(View):
    """图像验证码"""
    def get(self,request,uuid):

        hs,text,image=captcha.generate_captcha()

        redis_conn=get_redis_connection("verify_code")

        redis_conn.setex('img_%s'%uuid,300,text)

        return HttpResponse(image,content_type='img/jpg')


class SMSCodeView(View):
    """短信验证码"""
    def get(self,request,mobile):
        #接受参数
        image_code=request.GET.get('image_code')
        uuid=request.GET.get('image_code_id')

        if not all([image_code,uuid]):
            return JsonResponse({'code':400,'errmsg':"缺少必要参数"})
        #验证参数
        redis_conn=get_redis_connection("verify_code")
        image_code_redis=redis_conn.get('img_%s'%uuid)
        #判断短信验证码是否平凡发送
        msg_flag=redis_conn.get('flag_%s'%mobile)
        if msg_flag:
            return JsonResponse({'code':400,"errsmg":'请勿频繁发送'})

        if not image_code_redis:
            return JsonResponse({'code':400,"errsmg":'验证码过期了'})
        image_code_redis=image_code_redis.decode()

        #获取后删除验证码
        redis_conn.delete('img_%s'%uuid)
        # redis_conn.close()
        if image_code.lower()!=image_code_redis.lower():
            return JsonResponse({"code":400,'errmsg':"验证码错误"})

        #生成验证码
        msg_code='%06d'%random.randint(0,999999)
        #写入redis缓存库
        redis_conn.setex('msg_%s'%mobile,300,msg_code)

        redis_conn.setex('flag_%s'%mobile,60,1)
        #发送手机验证码
        # CCP().send_template_sms(mobile,[msg_code,5],1)
        ccp_send_msg_code.delay(mobile,msg_code)


        print(msg_code)




        return JsonResponse({'code':200,"msg":'ok'})
