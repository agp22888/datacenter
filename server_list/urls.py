from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.proof, name='proof'),
    path('list', views.servers, name='list'),
    # path('edit', views.edit, name='edit'),
    url(r'^edit/(?P<server_id>\d*)', views.edit, name='edit'),
    url(r'^view/(?P<server_id>\d*)', views.view, name='view'),
    url(r'^new', views.new, name='new'),
    url(r'^test_ajax/', views.test_ajax, name='test_ajax'),
    url(r'^all$', views.all, name='all'),
    url(r'^ip/(?P<ip_id>\d*)', views.edit_ip, name='edit_ip'),
]
