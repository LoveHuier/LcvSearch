import json
from django.shortcuts import render
from django.views.generic.base import View
# 用于把数据返回给前端
from django.http import HttpResponse
from search.models import LagouType, JobboleType
from elasticsearch import Elasticsearch

client = Elasticsearch(hosts=["127.0.0.1"])


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
    """
    完成自动搜索功能
    """

    def get(self, request):
        key_words = request.GET.get("q", "")
        # 多字段查询
        response = client.search(
            index="jobbole",
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["title", "tags", "content"]
                    }
                },
                # 用于做分页
                "from": 0,
                "size": 10,
                # key_words高亮
                # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-highlighting.html
                "highlight": {
                    # 设置高亮格式
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "content": {},
                        "title": {}
                    }
                }
            }
        )

        total_nums = response['hits']['total']
        hit_list = []
        for hit in response['hits']['hits']:
            hit_dict = {}
            if 'title' in hit["highlight"]:
                hit_dict["title"] = hit['highlight']['title']
            else:
                hit_dict["title"] = hit['_source']['title']
            if 'content' in hit["highlight"]:
                hit_dict['content'] = hit['highlight']['content'][:500]
            else:
                hit_dict["content"] = hit['_source']['content'][:500]

            hit_dict['create_date'] = hit['_source']["create_date"]
            hit_dict['url'] = hit['_source']['url']
            hit_dict['score'] = hit['_source']

            hit_list.append(hit_dict)

            data = {"all_hits": hit_list, "key_words": key_words}
            # 返回一个渲染后的httpresponse给前端
            return render(request, "result.html", data)
