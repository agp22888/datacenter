from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('list', views.servers, name='list'),
    # path('edit', views.edit, name='edit'),
    url(r'^server_edit/(?P<server_id>\d*)', views.server_edit, name='server_edit'),
    url(r'^server/$', views.server_view, name='server_view_without_parameters'),
    url(r'^server/(?P<server_id>\d*)', views.server_view, name='server_view'),
    url(r'^add_server', views.server_new, name='server_new'),
    url(r'^delete_server/(?P<server_id>\d*)', views.server_delete, name='server_delete'),

    url(r'^all$', views.server_view_all, name='server_view_all'),

    url(r'^ip/(?P<ip_id>\d*)', views.ip_edit, name='ip_edit'),
    url(r'^add_ip/(?P<server_id>\d*)', views.ip_new, name='ip_new'),

    url(r'^add_segment$', views.segment_new, name='segment_new'),
    url(r'^edit_segment/(?P<segment_id>\d*)', views.segment_edit, name='segment_edit'),

    url(r'ajax/', views.ajax, name='ajax'),

    url(r'rack/(?P<rack_id>\d*)', views.rack_view, name="rack_view"),
    url(r'rack_edit/?$', views.rack_edit, name="rack_edit"),
    # url(r'rack_edit/$', views.rack_edit, name="rack_edit_without_parameters"),
    # url(r'add_rack$', views.rack_new, name="rack_new"),

    url(r'room/(?P<room_id>\d*)', views.room_view, name="room_view"),
    url(r'room_edit/?$', views.room_edit, name="room_edit"),
    # url(r'room_edit/$', views.room_edit, name="room_edit_without_parameters"),
    # url(r'add_room$', views.room_new, name="room_new"),

    url(r'territory/(?P<territory_id>\d*)', views.territory_view, name="territory_view"),
    url(r'territory_edit/?$', views.territory_edit, name="territory_edit"),

    url(r'^test$', views.test, name='test'),

    url(r'^search$', views.search, name='search'),

    url(r'^login$', views.custom_login, name='custom_login'),
    url(r'^logout$', views.custom_logout, name='custom_logout'),

    url(r'^dump$', views.dump, name='dump'),

    url(r'^group_edit/?$', views.group_edit, name='group_edit'),
    # url(r'^add_group$', views.group_add, name='group_new'),
    # url(r'^group_edit/$', views.group_edit, name='group_edit_without_parameters'),

    url(r'^search_free', views.search_free_ip, name='search_free_ip')
]
