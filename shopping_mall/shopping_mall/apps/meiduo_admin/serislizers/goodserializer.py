from django.db import transaction
from rest_framework import serializers

from goods.models import SKU, SKUSpecification, GoodsCategory, SPU, SPUSpecification, SpecificationOption, Brand, \
    SKUImage


class SKUSpecModelSerializer(serializers.ModelSerializer):
    spec_id=serializers.IntegerField()
    option_id=serializers.IntegerField()

    class Meta:

        model=SKUSpecification
        fields=[
            "spec_id",
            'option_id'
        ]

class SKUGoodsModelSerializer(serializers.ModelSerializer):
    spu=serializers.StringRelatedField()
    spu_id=serializers.IntegerField()
    category=serializers.StringRelatedField()
    category_id=serializers.IntegerField()

    specs=SKUSpecModelSerializer(many=True)

    class Meta:
        model=SKU
        fields="__all__"

    # 默认模型类序列化器的create方法，无法帮助我们新建从表数据
    # specs = [{spec_id: "4", option_id: 8}, {spec_id: "5", option_id: 11}]
    def create(self, validated_data):
        specs = validated_data.pop('specs')
        # 默认的图片
        validated_data['default_image_url'] = "group1/M00/00/02/CtM3BVrRa8iAZdz1AAFZsBqChgk2188464"

        sku = None
        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                # 1、新建sku对象(主表)
                sku = SKU.objects.create(**validated_data)
                # 2、根据specs记录的新建sku规格和选项信息，插入中间表SKUSpecification数据
                for temp in specs:
                    # temp: {spec_id: "4", option_id: 8}
                    temp['sku_id'] = sku.id
                    SKUSpecification.objects.create(**temp)
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                raise e

            transaction.savepoint_commit(save_id)

        # 新增一个sku商品，对应生成静态化页面
        # generate_static_sku_detail_html.delay(sku.id)

        return sku


    def update(self, instance, validated_data):
        specs=validated_data.pop('specs')
        with transaction.atomic():
            save_id=transaction.savepoint()
            try:
                SKU.objects.filter(pk=instance.id).update(**validated_data)
                SKUSpecification.objects.filter(sku_id=instance.id).delete()
                for temp in specs:
                    # temp: {spec_id: "4", option_id: 8}
                    temp['sku_id'] = instance.id
                    SKUSpecification.objects.create(**temp)
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                raise e
            transaction.savepoint_commit(save_id)

        return instance



class SKUCategorieSerializer(serializers.ModelSerializer):
    """商品分类序列化器"""

    class Meta:
        model=GoodsCategory

        fields=[
            'id',
            'name'
        ]



class SPUSimpleSerializer(serializers.ModelSerializer):
    """商品spu序列化器"""
    class Meta:
        model=SPU
        fields=[
            'id',
            'name'
        ]




class SPUOptineSerializer(serializers.ModelSerializer):
    """规格选项序列化"""
    class Meta:
        model=SpecificationOption
        fields=[
            'id',
            'value'
        ]


class SPUSpecSerializer(serializers.ModelSerializer):

    """规格序列化"""

    spu=serializers.StringRelatedField()
    spu_id=serializers.IntegerField()
    options=SPUOptineSerializer(many=True)
    class Meta:
        model=SPUSpecification
        fields=[
            'id',
            'name',
            'spu',
            'spu_id',
            'options'
        ]




class SPUGoodsSerializer(serializers.ModelSerializer):
    brand=serializers.StringRelatedField()
    brand_id=serializers.IntegerField()
    category1_id=serializers.IntegerField()
    category2_id=serializers.IntegerField()
    category3_id=serializers.IntegerField()
    class Meta:
        model=SPU
        exclude=('category1','category2','category3')


class SPUBrandsSerializer(serializers.ModelSerializer):
    """
         SPU表品牌序列化器
     """
    class Meta:
        model=Brand
        fields=[
            'id',
            'name'
        ]

class CategorySerializer(serializers.ModelSerializer):
    " SPU表分类信息获取序列化器"

    class Meta:
        model=GoodsCategory
        fields=[
            'id',
            'name'
        ]



#规格表管理

class SPUSpecificationSerializer(serializers.ModelSerializer):
    "关联嵌套返回spu表的商品名"
    spu=serializers.StringRelatedField()
    spu_id=serializers.IntegerField()
    class Meta:
        model=SPUSpecification
        fields=[
            'id',
            'name',
            'spu',
            'spu_id'
        ]




#规格选项管理
class OptionSerializer(serializers.ModelSerializer):
    spec=serializers.StringRelatedField()
    spec_id=serializers.IntegerField()
    class Meta:
        model=SpecificationOption
        fields=[
            'id',
            'value',
            'spec',
            'spec_id'
        ]

class OptionSpecificationSerializer(serializers.ModelSerializer):

    class Meta:
        model=SPUSpecification
        fields=[
            'id',
            'name'
        ]






#图片管理

class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model=SKUImage
        fields=[
            'id',
            'sku',
            'image'
        ]

class SKUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model=SKU
        fields=[
            'id',
            'name'
        ]