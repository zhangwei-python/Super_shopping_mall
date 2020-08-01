from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings

# Create your models here.
from shopping_mall.utils.BaseModel import BaseModel


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
    default_address = models.ForeignKey('Address',
                                        related_name='users',
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        verbose_name='默认地址')

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


class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='addresses',
                             verbose_name='用户')

    province = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='province_addresses',
                                 verbose_name='省')

    city = models.ForeignKey('areas.Area',
                             on_delete=models.PROTECT,
                             related_name='city_addresses',
                             verbose_name='市')

    district = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='district_addresses',
                                 verbose_name='区')

    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20,
                           null=True,
                           blank=True,
                           default='',
                           verbose_name='固定电话')

    email = models.CharField(max_length=30,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='电子邮箱')

    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_addresses'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']