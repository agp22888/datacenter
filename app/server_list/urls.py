from django.urls import path, re_path
from django.views.generic import RedirectView

# from django.conf.urls import url
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='list')),
    path('list', views.servers, name='list'),
    # path('edit', views.edit, name='edit'),
    re_path(r'^server_edit/?$', views.server_edit, name='server_edit'),
    re_path(r'^server/$', views.server_view, name='server_view_without_parameters'),
    re_path(r'^server/(?P<server_id>\d*)', views.server_view, name='server_view'),
    # url(r'^add_server', views.server_new, name='server_new'),
    re_path(r'^delete_server/(?P<server_id>\d*)', views.server_delete, name='server_delete'),

    re_path(r'^all$', views.server_view_all, name='server_view_all'),

    re_path(r'^ip/?$', views.ip_edit, name='ip_edit'),
    # url(r'^add_ip/(?P<server_id>\d*)', views.ip_new, name='ip_new'),

    # url(r'^add_segment$', views.segment_new, name='segment_new'),
    re_path(r'^segment_edit/?$', views.segment_edit, name='segment_edit'),

    re_path(r'ajax/', views.ajax, name='ajax'),

    # re_path(r'rack/(?P<rack_id>\d*)', views.rack_view, name="rack_view"),
    # re_path(r'rack_edit/?$', views.rack_edit, name="rack_edit"),
    re_path(r'rack/(?P<rack_id>\d*)', views.RackView.as_view(), name="rack_view"),
    re_path(r'rack_edit/?$', views.RackEdit.as_view(), name="rack_edit"),
    # url(r'rack_edit/$', views.rack_edit, name="rack_edit_without_parameters"),
    # url(r'add_rack$', views.rack_new, name="rack_new"),

    re_path(r'room/(?P<room_id>\d*)', views.room_view, name="room_view"),
    re_path(r'room_edit/?$', views.room_edit, name="room_edit"),
    # url(r'room_edit/$', views.room_edit, name="room_edit_without_parameters"),
    # url(r'add_room$', views.room_new, name="room_new"),

    re_path(r'territory/(?P<territory_id>\d*)', views.territory_view, name="territory_view"),
    re_path(r'territory_edit/?$', views.territory_edit, name="territory_edit"),


    re_path(r'^search$', views.search, name='search'),

    re_path(r'^login$', views.custom_login, name='custom_login'),
    re_path(r'^logout$', views.custom_logout, name='custom_logout'),

    re_path(r'^dump$', views.dump, name='dump'),

    re_path(r'^group_edit/?$', views.group_edit, name='group_edit'),
    # url(r'^add_group$', views.group_add, name='group_new'),
    # url(r'^group_edit/$', views.group_edit, name='group_edit_without_parameters'),

    re_path(r'^search_free', views.search_free_ip, name='search_free_ip')
]
