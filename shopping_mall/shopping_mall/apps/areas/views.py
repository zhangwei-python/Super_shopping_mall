from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from areas.models import Area


class ProvinceAreasView(View):
    """获取省分信息"""
    def get(self,request):
        #查询数据
        provinces=Area.objects.filter(parent_id=None)
        province_list=[]

        for province in provinces:
            province_list.append({
                "id":province.id,
                "name":province.name
            })

        #换回数据
        return JsonResponse({
            "code":0,
            'errmsg':"ok",
            'province_list':province_list

        })


class SubAreasView(View):
    """获取市区信息"""
    def get(self,request,pk):
        #查询数据
        subs=Area.objects.filter(parent_id=pk)
        province=Area.objects.get(id=pk)

        sub_list=[]
        for sub in subs:
            sub_list.append({
                'id':sub.id,
                "name":sub.name
            })

        sub_data={
            'id':province.id,
            'name':province.name,
            'subs':sub_list
        }

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'sub_data':sub_data
        })



