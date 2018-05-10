import json
from django.shortcuts import render
from django.views.generic.base import View

# 用于把数据返回给前端
from django.http import HttpResponse

from search.models import LagouType,JobboleType


# Create your views here.
class SearchSuggest(View):
    """
    搜索补全功能
    """

    def get(self, request):
        key_words = request.GET.get('s', '')
        re_datas = []
        if key_words:
            s = JobboleType.search()  # 实例化elasticsearch(搜索引擎)类的search查询
            s = s.suggest("my_suggest", key_words, completion={
                "field": "suggest",
                "fuzzy": {
                    "fuzziness": 1
                },
                "size": 10
            })

            suggestions = s.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_datas.append(source["title"])

        return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(View):
    def get(self, request):

        pass
