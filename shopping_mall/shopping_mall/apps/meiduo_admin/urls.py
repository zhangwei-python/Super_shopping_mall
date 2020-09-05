from django.urls import re_path
from rest_framework_jwt.views import obtain_jwt_token
from meiduo_admin.views import home_views, user_views, goods_views, order_views, auth_views

urlpatterns=[
    re_path(r'^authorizations/$',obtain_jwt_token),
    re_path(r'^statistical/total_count/$',home_views.UserTotalCountView.as_view()),
    re_path(r'^statistical/day_increment/$',home_views.UserDayCountView.as_view()),
    re_path(r'^statistical/day_active/$',home_views.UserActiveCountView.as_view()),
    re_path(r'^statistical/day_orders/$',home_views.UserOrderCountView.as_view()),
    re_path(r'^statistical/month_increment/$',home_views.UserMonthCountView.as_view()),
    re_path(r'^statistical/goods_day_views/$',home_views.GoodsDayView.as_view()),
    re_path(r'^users/$',user_views.UserView.as_view()),

    #sku管理
    re_path(r'^skus/$',goods_views.SKUGoodsView.as_view({'get':'list','post':'create'})),
    re_path(r'^skus/(?P<pk>\d+)/$',goods_views.SKUGoodsView.as_view({'get':'retrieve','put':'update','delete':'destroy'})),
    re_path(r'^skus/categories/$',goods_views.SKUCategorieView.as_view()),
    re_path(r'^goods/simple/',goods_views.SPUSimpleView.as_view()),
    re_path(r'^goods/(?P<pk>\d+)/specs/',goods_views.SPUSpecView.as_view()),
    #spu标管理
    re_path(r'^goods/$',goods_views.SPUGoodsView.as_view({'get':'list','post':'create'})),
    re_path(r'^goods/(?P<pk>\d+)/$',goods_views.SPUGoodsView.as_view({'get':'retrieve','put':'update','delete':'destroy'})),
    re_path(r'^goods/brands/simple/$',goods_views.SPUBrandView.as_view()),
    re_path(r'^goods/channel/categories/$',goods_views.ChannelCategoryView.as_view()),
    re_path(r'^goods/channel/categories/(?P<pk>\d+)/$',goods_views.ChannelCategoryView.as_view()),
    #re_path(r'^goods/specs/$',goods_views.SpecsView.as_view({'get':'list','post':'create'}))
    re_path(r'^goods/specs/simple/$',goods_views.OptionSimple.as_view()),
    #订单
    re_path(r'^orders/$', order_views.OrderView.as_view({'get': 'list'})),
    re_path(r'^orders/(?P<pk>\d+)/$', order_views.OrderView.as_view({'get': 'retrieve'})),
    re_path(r'^orders/(?P<pk>\d+)/status/$', order_views.OrderView.as_view({'patch': 'partial_update'})),

    re_path(r"^skus/simple/$",goods_views.SKUSimpleView.as_view()),
    re_path(r'^permission/content_types/$',auth_views.ContentTypeView.as_view()),
    re_path(r'permission/simple/$',auth_views.CroupPermView.as_view()),
    re_path(r'^permission/groups/simple/$',auth_views.AdminGroupView.as_view())
]

from rest_framework.routers import SimpleRouter

router=SimpleRouter()
#规格管理表
router.register(prefix='goods/specs',viewset=goods_views.SpecsView,basename='goods')
#规格选项表
router.register(prefix='specs/options',viewset=goods_views.OptionsView,basename='option')
#订单
# router.register(prefix='orders',viewset=order_views.OrderView,basename='order')
#图片管理
router.register(prefix='skus/images',viewset=goods_views.ImageView,basename='image')
#权限组管理
router.register(prefix='permission/perms',viewset=auth_views.PermissionView,basename='permission')
#用户组管理
router.register(prefix='permission/groups',viewset=auth_views.GroupView,basename='group')
#管理员
router.register(prefix='permission/admins',viewset=auth_views.AdminView,basename='admin')
urlpatterns+=router.urls