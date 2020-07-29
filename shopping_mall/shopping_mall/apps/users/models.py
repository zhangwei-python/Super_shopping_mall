from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings

# Create your models here.
class User(AbstractUser):
    mobile=models.CharField(
        unique=True,
        verbose_name='手机号',
        null=True,
        max_length=11
    )

    email_active=models.BooleanField(
        default=False,
        verbose_name="邮箱激活状态"

    )

    class Meta:
        db_table='tb_users'
        verbose_name='手机号',
        verbose_name_plural='手机号'

    def __str__(self):
        return self.username

    def generate_verify_email_url(self):
        """生成当前用户令牌，并返回链接"""
        serializer=TimedJSONWebSignatureSerializer(secret_key=settings.SECRET_KEY)
        user_info={'user_id':self.id,"email":self.email}
        token=serializer.dumps(user_info)

        verify_url=settings.EMAIL_VERIFY_URL+token.decode()
        return verify_url


    @staticmethod
    def check_verify_email_token(token):
        """
        检验token值
        :return: 对象或None
        """
        se=TimedJSONWebSignatureSerializer(secret_key=settings.SECRET_KEY)
        try:
            usr_info=se.loads(token)
        except Exception as e:
            print(e)
            return None
        try:
            user=User.objects.get(pk=usr_info.get('user_id'))


        except Exception as e:
            print(e)
            return None
        return user