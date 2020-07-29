from django.contrib.auth.backends import ModelBackend
from .models import User

class UsernameMobileAuthBackend(ModelBackend):
    """重写authnticate方法，实现多账号登录"""

    def authenticate(self, request, username=None, password=None, **kwargs):

        try:
            user=User.objects.get(username=username)
        except:
            try:
                user=User.objects.get(mobile=username)
            except:
                return None
        if user.check_password(password):
            return user

