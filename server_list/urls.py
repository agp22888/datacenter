from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.proof, name='proof'),
    path('list', views.servers, name='list'),
    # path('edit', views.edit, name='edit'),
    url(r'^edit/(?P<server_id>\d*)', views.server_edit, name='server_edit'),
    url(r'^view/(?P<server_id>\d*)', views.server_view, name='server_view'),
    url(r'^new_server', views.server_new, name='server_new'),
    url(r'^test_ajax/', views.test_ajax, name='test_ajax'),
    url(r'^all$', views.server_view_all, name='server_view_all'),
    url(r'^ip/(?P<ip_id>\d*)', views.ip_edit, name='ip_edit'),
    url(r'^new_ip/(?P<server_id>\d*)', views.ip_new, name='ip_new'),
    url(r'^new_segment$', views.segment_new, name='segment_new'),
    url(r'^view_segment/(?P<segment_id>\d*)', views.segment_view, name='segment_view'),
    # todo подумать над объединением view для создания и редактирования объекта
    # url(r'^edit_segment/(?P<segment_id>\d*)', views.segment_edit, name='segment_edit'),
    url(r'^edit_segment_test/(?P<segment_id>\d*)', views.segment_edit, name='segment_edit_test'),
    url(r'ajax/', views.ajax, name='ajax'),
]
