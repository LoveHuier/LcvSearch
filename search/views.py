import json
import redis
from django.shortcuts import render
from django.views.generic.base import View
# 用于把数据返回给前端
from django.http import HttpResponse
from search.models import LagouType, JobboleType
from datetime import datetime
from elasticsearch import Elasticsearch

client = Elasticsearch(hosts=["127.0.0.1"])

redis_cli = redis.StrictRedis(host="127.0.0.1")


class IndexView(View):
    """
    要在网页中加逻辑，必须重写View，不能使用django默认提供的TemplateView
    """

    def get(self, request):
        # 逆序排列所有成员,并取出前5位
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        return render(request, "index.html", {"topn_search": topn_search})


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

        # 效率很高，因为它将数据保存到内存当中
        redis_cli.zincrby("search_keywords_set", key_words)

        # 逆序排列所有成员,并取出前5位
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)

        # 判断请求的是第几页数据
        page = request.GET.get("p", "1")
        try:
            page = int(page)
        except:
            page = 1

        jobbole_count = redis_cli.get("jobbole_count")

        # 计时
        start_time = datetime.now()

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
                "from": (page - 1) * 10,
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

        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()

        total_nums = response['hits']['total']
        if (page % 10) > 0:
            page_nums = int(total_nums / 10) + 1
        else:
            page_nums = int(total_nums / 10)

        hit_list = []
        for hit in response['hits']['hits']:
            hit_dict = {}
            if 'title' in hit["highlight"]:
                hit_dict["title"] = "".join(hit['highlight']['title'])
            else:
                hit_dict["title"] = hit['_source']['title']
            if 'content' in hit["highlight"]:
                hit_dict['content'] = "".join(hit['highlight']['content'][:500])
            else:
                hit_dict["content"] = hit['_source']['content'][:500]

            hit_dict['create_date'] = hit['_source']["create_date"]
            hit_dict['url'] = hit['_source']['url']
            hit_dict['score'] = hit['_score']

            hit_list.append(hit_dict)

        # 返回一个渲染后的httpresponse给前端
        return render(request, "result.html", {"all_hits": hit_list,
                                               "key_words": key_words,
                                               "total_nums": total_nums,
                                               "page": page,
                                               "page_nums": page_nums,
                                               "last_seconds": last_seconds,
                                               "jobbole_count": jobbole_count,
                                               "topn_search": topn_search})
