"""LcvSearch URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path  # 此处应用path，老板本使用的是url
from django.views.generic import TemplateView
from search.views import SearchSuggest

urlpatterns = [
    # path('admin/', admin.site.urls),
    # 此处设置为首页，以前写法是'^$',新版本不再使用^、$，只需要‘’就可以
    path("", TemplateView.as_view(template_name="index.html"), name='index'),

    path("suggest/", SearchSuggest.as_view(), name='suggest'),
    path("search/", SearchSuggest.as_view(), name='suggest')
]
