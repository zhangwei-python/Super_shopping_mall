from orders.models import *
from rest_framework import serializers

class OrderSerializer(serializers.ModelSerializer):
    "订单"
    class Meta:
        model=OrderInfo
        fields=[
            'order_id',
            'create_time'
        ]





class SKUSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model=SKU
        fields=[
            'name',
            'default_image_url'
        ]

class OrderGoodsSerializer(serializers.ModelSerializer):
    sku=SKUSimpleSerializer()
    class Meta:
        model=OrderGoods
        fields=[
            'count',
            'price',
            'sku'
        ]

#订单详情页
class OrderDetailSerializer(serializers.ModelSerializer):

    user=serializers.StringRelatedField()
    skus=OrderGoodsSerializer(many=True)

    class Meta:
        model=OrderInfo
        fields="__all__"