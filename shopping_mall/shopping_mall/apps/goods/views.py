from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from goods.models import GoodsCategory, SKU


def get_breadcrumb(category):
    dict={}
    #判断是哪个级别
    if category.parent is None:
        #第一类级别
        dict['cat1']=category.name
    elif category.parent.parent is None:
        #第二级别
        dict['cat2']=category.name
        dict['cat1']=category.parent.name
    else:
        #第三级
        dict['cat3']=category.name
        dict['cat2']=category.parent.name
        dict['cat1']=category.parent.parent.name
    return dict






class ListView(View):
    """商品列表页"""
    def get(self,request,category_id):
        #获取参数
        page=request.GET.get('page')
        page_size=request.GET.get('page_size')
        ordering=request.GET.get('ordering')


        try:
            category=GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse(
                {'code':400,
                 'errmsg':'获取数据失败'}
            )
        #面包屑导航
        breadcrumb=get_breadcrumb(category)

        skus=SKU.objects.filter(category=category,
                               is_launched=True).order_by(ordering)
        paginator=Paginator(skus,page_size)

        #获取煤业商品数据
        try:
            page_skus=paginator.page(page)
        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':'page数据出错'
            })

        list=[]
        for sku in skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url.url,
                'name':sku.name,
                'price':sku.price
            })
        # print(list)

        total_page=paginator.num_pages

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            "breadcrumb":breadcrumb,
            'list':list,
            'count':total_page
        })


class HotGoodsView(View):
    #热销商品
    def get(self,request,category_id):
        skus=SKU.objects.filter(category_id=category_id,
                               is_launched=True).order_by('-sales')[:2]
        hot_skus=[]
        for sku in skus:
            hot_skus.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url.url,
                'name':sku.name,
                'price':sku.price
            })

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'hot_skus':hot_skus
        })




from haystack.views import SearchView
class MySearchView(SearchView):
    # 当前搜索是"短语精确搜索" —— 不会把用户的搜索词进行分词处理；
    # 构建一个响应
    def create_response(self):
        # 默认SearchView搜索视图逻辑：先搜索出结果，再调用create_response函数构建响应
        # 1、获取全文检索的结果
        context = self.get_context()

        # context['query'] 检索词
        # context['paginator'] 分页器对象
        # context['paginator'].count 数据量
        # context['paginator'].num_pages 当前页
        # context['page'].object_list 列表(SearchResult对象)
        # SearchResult.object 被搜索到的SKU模型类对象

        sku_list = []
        # 2、从查询的结果context中提取查询到的sku商品数据
        for search_result in context['page'].object_list:
            # search_result: SearchResult对象
            # search_result.object: SKU模型类对象
            sku = search_result.object
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image_url.url,
                'searchkey': context['query'],
                'page_size': context['paginator'].per_page,
                'count': context['paginator'].count
            })

        return JsonResponse(sku_list, safe=False)