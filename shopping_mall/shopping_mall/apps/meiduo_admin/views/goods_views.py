
from rest_framework.viewsets import ModelViewSet

from meiduo_admin.mypagination import Mypage
from meiduo_admin.serislizers.goodserializer import *

class SKUGoodsView(ModelViewSet):
    """商品sku"""
    queryset = SKU.objects.all()
    serializer_class = SKUGoodsModelSerializer
    pagination_class = Mypage

    def get_queryset(self):
        keyword=self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()



from rest_framework.generics import ListAPIView
class SKUCategorieView(ListAPIView):
    "分类选择"
    queryset = GoodsCategory.objects.all()
    serializer_class = SKUCategorieSerializer

    def get_queryset(self):
        return self.queryset.filter(parent_id__gte=37)






class SPUSimpleView(ListAPIView):
    """spu商品名称"""
    queryset = SPU.objects.all()
    serializer_class = SPUSimpleSerializer



class SPUSpecView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecSerializer
    def get_queryset(self):
        pk=self.kwargs['pk']

        return self.queryset.filter(spu_id=pk)






#spu表管理
class SPUGoodsView(ModelViewSet):
    queryset = SPU.objects.all()
    serializer_class = SPUGoodsSerializer
    pagination_class = Mypage

    def get_queryset(self):
        keyword=self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()

class SPUBrandView(ListAPIView):
    " 获取SPU表的品牌信息"
    queryset = Brand.objects.all()
    serializer_class = SPUBrandsSerializer

class ChannelCategoryView(ListAPIView):
    queryset = GoodsCategory.objects.all()
    serializer_class =CategorySerializer
    def get_queryset(self):
        pk=self.kwargs.get('pk')
        if pk:
            return self.queryset.filter(parent_id=pk)
        return self.queryset.filter(parent_id=None)




#规格表管理
class SpecsView(ModelViewSet):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecificationSerializer
    pagination_class = Mypage



#规格选项表
class OptionsView(ModelViewSet):
    queryset = SpecificationOption.objects.all()
    serializer_class = OptionSerializer
    pagination_class = Mypage


class OptionSimple(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class =OptionSpecificationSerializer





#图片管理
class ImageView(ModelViewSet):
    queryset = SKUImage.objects.all()
    serializer_class = ImageSerializer
    pagination_class = Mypage



class SKUSimpleView(ListAPIView):
    queryset = SKU.objects.all()
    serializer_class = SKUSimpleSerializer