from django.conf.urls import include, url
from django.contrib import admin
from . import views

app_name = 'plot'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^plot/search_results/$', views.search_results, name='search_results'),
    url(r'^plot/abstract/$', views.abstract, name='abstract'),
]