from django.conf.urls import url

from . import views

urlpatterns = [
    url('scrap', views.index, name='index'),
    url('^search', views.return_searched_app_name, name='return_searched_app_name'),
    url('^detail', views.return_detail_of_app, name='return_detail_of_app'),
]