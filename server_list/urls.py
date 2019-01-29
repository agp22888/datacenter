from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.proof, name='proof'),
    path('list', views.servers, name='list'),
    # path('edit', views.edit, name='edit'),
    url(r'^edit/(?P<server_id>\d*)', views.server_edit, name='server_edit'),
    url(r'^view/(?P<server_id>\d*)', views.server_view, name='server_view'),
    url(r'^new', views.server_new, name='server_new'),
    url(r'^test_ajax/', views.test_ajax, name='test_ajax'),
    url(r'^all$', views.server_view_all, name='server_view_all'),
    url(r'^ip/(?P<ip_id>\d*)', views.ip_edit, name='ip_edit'),
]
